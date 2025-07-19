"""Smart token budget manager for optimal content allocation."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..analyzers.priority_analyzer import PriorityLevel


class BudgetStrategy(Enum):
    """Budget allocation strategies."""

    CONSERVATIVE = "conservative"  # Reserve more tokens for critical content
    BALANCED = "balanced"  # Balanced allocation across priority levels
    AGGRESSIVE = "aggressive"  # More tokens for medium/low priority content


@dataclass
class CondensingAdjustment:
    """Represents a suggested adjustment to condensing level."""

    file_path: Path
    current_level: str
    suggested_level: str
    reason: str
    tokens_saved: int


@dataclass
class BudgetAllocation:
    """Represents token budget allocation for a file."""

    file_path: Path
    priority: PriorityLevel
    allocated_tokens: int
    estimated_content_tokens: int
    condensing_level: str
    is_critical_preserve: bool = False
    actual_tokens: int = 0
    efficiency: float = 0.0


class SmartTokenBudgetManager:
    """Manages token budgets intelligently to minimize truncation."""

    def __init__(
        self,
        total_token_limit: int,
        strategy: BudgetStrategy = BudgetStrategy.BALANCED,
        reserve_ratio: float = 0.1,
    ):
        """Initialize the budget manager.

        Args:
            total_token_limit: Total token limit for the output
            strategy: Budget allocation strategy
            reserve_ratio: Ratio of tokens to reserve for metadata/formatting
        """
        self.total_token_limit = total_token_limit
        self.strategy = strategy
        self.reserve_ratio = reserve_ratio

        # Reserve tokens for metadata, formatting, etc.
        self.reserved_tokens = int(total_token_limit * reserve_ratio)
        self.available_tokens = total_token_limit - self.reserved_tokens

        # Track usage
        self.allocated_tokens = 0
        self.used_tokens = 0
        self.file_allocations: dict[Path, BudgetAllocation] = {}
        self.usage_history: list[tuple[Path, int]] = []

    def allocate_budget(
        self,
        file_priorities: dict[Path, PriorityLevel],
        file_token_estimates: dict[Path, int],
        import_scores: dict[Path, float] | None = None,
    ) -> dict[Path, BudgetAllocation]:
        """Allocate token budget across files based on priorities.

        Args:
            file_priorities: Mapping of file paths to priority levels
            file_token_estimates: Estimated tokens for each file
            import_scores: Optional import importance scores

        Returns:
            Dictionary mapping file paths to budget allocations
        """
        # Calculate priority weights based on strategy
        priority_weights = self._get_priority_weights()

        # Calculate total weighted demand
        total_weighted_demand = 0.0
        for file_path, priority in file_priorities.items():
            base_tokens = file_token_estimates.get(file_path, 0)
            import_boost = (
                1.0 + (import_scores.get(file_path, 0.0) * 0.5)
                if import_scores
                else 1.0
            )
            weight = priority_weights[priority] * import_boost
            total_weighted_demand += base_tokens * weight

        # Allocate tokens proportionally
        allocations = {}
        critical_files = []

        for file_path, priority in file_priorities.items():
            estimated_tokens = file_token_estimates.get(file_path, 0)
            import_boost = (
                1.0 + (import_scores.get(file_path, 0.0) * 0.5)
                if import_scores
                else 1.0
            )
            weight = priority_weights[priority] * import_boost

            if total_weighted_demand > 0:
                proportion = (estimated_tokens * weight) / total_weighted_demand
                allocated = int(self.available_tokens * proportion)
            else:
                allocated = estimated_tokens

            # Determine condensing level
            condensing_level = self._determine_condensing_level(
                priority, allocated, estimated_tokens
            )

            # Mark critical files for full preservation if possible
            is_critical_preserve = (
                priority == PriorityLevel.CRITICAL
                and allocated >= estimated_tokens * 0.9
            )

            if priority == PriorityLevel.CRITICAL:
                critical_files.append(file_path)

            allocation = BudgetAllocation(
                file_path=file_path,
                priority=priority,
                allocated_tokens=allocated,
                estimated_content_tokens=estimated_tokens,
                condensing_level=condensing_level,
                is_critical_preserve=is_critical_preserve,
            )

            allocations[file_path] = allocation
            self.file_allocations[file_path] = allocation
            self.allocated_tokens += allocated

        # Ensure critical files get minimum required allocation
        self._ensure_critical_file_budgets(allocations, critical_files)

        return allocations

    def track_usage(self, file_path: Path, tokens_used: int) -> None:
        """Track actual token usage for a file.

        Args:
            file_path: Path to the file
            tokens_used: Number of tokens actually used
        """
        self.used_tokens += tokens_used
        self.usage_history.append((file_path, tokens_used))

        # Update allocation if it exists
        if file_path in self.file_allocations:
            allocation = self.file_allocations[file_path]
            # Track efficiency (how well we estimated)
            efficiency = (
                tokens_used / allocation.allocated_tokens
                if allocation.allocated_tokens > 0
                else 0
            )

            # Store efficiency for future improvements
            allocation.actual_tokens = tokens_used
            allocation.efficiency = efficiency

    def get_remaining_budget(self) -> int:
        """Get remaining token budget.

        Returns:
            Number of tokens remaining in budget
        """
        return max(0, self.total_token_limit - self.used_tokens - self.reserved_tokens)

    def suggest_adjustments(self) -> list[CondensingAdjustment]:
        """Suggest adjustments to condensing levels based on usage.

        Returns:
            List of suggested adjustments
        """
        adjustments = []
        remaining_budget = self.get_remaining_budget()

        # If we're over budget, suggest more aggressive condensing
        if remaining_budget < 0:
            over_budget = abs(remaining_budget)
            adjustments.extend(self._suggest_budget_reduction(over_budget))

        # If we have significant budget remaining, suggest less condensing
        elif remaining_budget > self.available_tokens * 0.2:
            adjustments.extend(self._suggest_budget_expansion(remaining_budget))

        return adjustments

    def get_budget_report(self) -> dict:
        """Generate a detailed budget report.

        Returns:
            Dictionary containing budget analysis
        """
        total_estimated = sum(
            alloc.estimated_content_tokens for alloc in self.file_allocations.values()
        )

        priority_breakdown = {}
        for priority in PriorityLevel:
            priority_files = [
                alloc
                for alloc in self.file_allocations.values()
                if alloc.priority == priority
            ]
            priority_breakdown[priority.name] = {
                "count": len(priority_files),
                "allocated_tokens": sum(f.allocated_tokens for f in priority_files),
                "estimated_tokens": sum(
                    f.estimated_content_tokens for f in priority_files
                ),
            }

        return {
            "total_limit": self.total_token_limit,
            "reserved_tokens": self.reserved_tokens,
            "available_tokens": self.available_tokens,
            "allocated_tokens": self.allocated_tokens,
            "used_tokens": self.used_tokens,
            "remaining_budget": self.get_remaining_budget(),
            "total_estimated": total_estimated,
            "compression_ratio": self.allocated_tokens / total_estimated
            if total_estimated > 0
            else 0,
            "priority_breakdown": priority_breakdown,
            "efficiency": self.used_tokens / self.allocated_tokens
            if self.allocated_tokens > 0
            else 0,
        }

    def _get_priority_weights(self) -> dict[PriorityLevel, float]:
        """Get priority weights based on strategy."""
        if self.strategy == BudgetStrategy.CONSERVATIVE:
            return {
                PriorityLevel.CRITICAL: 1.0,
                PriorityLevel.HIGH: 0.6,
                PriorityLevel.MEDIUM: 0.3,
                PriorityLevel.LOW: 0.1,
                PriorityLevel.MINIMAL: 0.05,
            }
        elif self.strategy == BudgetStrategy.AGGRESSIVE:
            return {
                PriorityLevel.CRITICAL: 1.0,
                PriorityLevel.HIGH: 0.8,
                PriorityLevel.MEDIUM: 0.6,
                PriorityLevel.LOW: 0.4,
                PriorityLevel.MINIMAL: 0.2,
            }
        else:  # BALANCED
            return {
                PriorityLevel.CRITICAL: 1.0,
                PriorityLevel.HIGH: 0.7,
                PriorityLevel.MEDIUM: 0.4,
                PriorityLevel.LOW: 0.2,
                PriorityLevel.MINIMAL: 0.1,
            }

    def _determine_condensing_level(
        self, priority: PriorityLevel, allocated_tokens: int, estimated_tokens: int
    ) -> str:
        """Determine appropriate condensing level based on allocation."""
        if allocated_tokens >= estimated_tokens * 0.9:
            return "none"  # Minimal or no condensing
        elif allocated_tokens >= estimated_tokens * 0.7:
            return "light"  # Light condensing
        elif allocated_tokens >= estimated_tokens * 0.5:
            return "moderate"  # Moderate condensing
        elif allocated_tokens >= estimated_tokens * 0.3:
            return "heavy"  # Heavy condensing
        else:
            return "maximum"  # Maximum condensing

    def _ensure_critical_file_budgets(
        self, allocations: dict[Path, BudgetAllocation], critical_files: list[Path]
    ) -> None:
        """Ensure critical files have adequate budget allocation."""
        for file_path in critical_files:
            allocation = allocations[file_path]

            # Critical files should get at least 80% of their estimated tokens
            min_required = int(allocation.estimated_content_tokens * 0.8)

            if allocation.allocated_tokens < min_required:
                shortfall = min_required - allocation.allocated_tokens

                # Try to reallocate from lower priority files
                redistributed = self._redistribute_tokens(
                    allocations, shortfall, exclude=critical_files
                )

                allocation.allocated_tokens += redistributed
                self.allocated_tokens += redistributed

    def _redistribute_tokens(
        self,
        allocations: dict[Path, BudgetAllocation],
        tokens_needed: int,
        exclude: list[Path],
    ) -> int:
        """Redistribute tokens from lower priority files."""
        redistributed = 0

        # Sort files by priority (lowest first) and exclude critical files
        non_critical = [
            (path, alloc)
            for path, alloc in allocations.items()
            if path not in exclude and alloc.priority != PriorityLevel.CRITICAL
        ]
        non_critical.sort(key=lambda x: x[1].priority.value, reverse=True)

        for _file_path, allocation in non_critical:
            if redistributed >= tokens_needed:
                break

            # Take up to 30% of allocation from lower priority files
            available = int(allocation.allocated_tokens * 0.3)
            take = min(available, tokens_needed - redistributed)

            allocation.allocated_tokens -= take
            redistributed += take

        return redistributed

    def _suggest_budget_reduction(self, over_budget: int) -> list[CondensingAdjustment]:
        """Suggest ways to reduce token usage when over budget."""
        adjustments = []

        # Prioritize condensing lower priority files more aggressively
        for allocation in sorted(
            self.file_allocations.values(), key=lambda x: x.priority.value, reverse=True
        ):
            if over_budget <= 0:
                break

            current_level = allocation.condensing_level
            if current_level in ["none", "light"]:
                suggested_level = "moderate"
                estimated_savings = int(allocation.estimated_content_tokens * 0.3)
            elif current_level == "moderate":
                suggested_level = "heavy"
                estimated_savings = int(allocation.estimated_content_tokens * 0.2)
            elif current_level == "heavy":
                suggested_level = "maximum"
                estimated_savings = int(allocation.estimated_content_tokens * 0.15)
            else:
                continue  # Already at maximum

            adjustments.append(
                CondensingAdjustment(
                    file_path=allocation.file_path,
                    current_level=current_level,
                    suggested_level=suggested_level,
                    reason=f"Reduce budget usage by ~{estimated_savings} tokens",
                    tokens_saved=estimated_savings,
                )
            )

            over_budget -= estimated_savings

        return adjustments

    def _suggest_budget_expansion(
        self, surplus_budget: int
    ) -> list[CondensingAdjustment]:
        """Suggest ways to use surplus budget for better content quality."""
        adjustments = []

        # Prioritize expanding higher priority files first
        for allocation in sorted(
            self.file_allocations.values(), key=lambda x: x.priority.value
        ):
            if surplus_budget <= 0:
                break

            current_level = allocation.condensing_level
            if current_level == "maximum":
                suggested_level = "heavy"
                estimated_cost = int(allocation.estimated_content_tokens * 0.15)
            elif current_level == "heavy":
                suggested_level = "moderate"
                estimated_cost = int(allocation.estimated_content_tokens * 0.2)
            elif current_level == "moderate":
                suggested_level = "light"
                estimated_cost = int(allocation.estimated_content_tokens * 0.2)
            elif current_level == "light":
                suggested_level = "none"
                estimated_cost = int(allocation.estimated_content_tokens * 0.2)
            else:
                continue  # Already at minimum condensing

            if estimated_cost <= surplus_budget:
                adjustments.append(
                    CondensingAdjustment(
                        file_path=allocation.file_path,
                        current_level=current_level,
                        suggested_level=suggested_level,
                        reason="Use surplus budget to improve content quality",
                        tokens_saved=-estimated_cost,  # Negative means tokens consumed
                    )
                )

                surplus_budget -= estimated_cost

        return adjustments
