class Folder2md4llms < Formula
  desc "Enhanced tool to concatenate folder contents into markdown for LLM consumption"
  homepage "https://github.com/henriqueslab/folder2md4llms"
  version "0.4.38"
  license "MIT"

  # Binary distribution from GitHub releases
  on_macos do
    if Hardware::CPU.intel?
      url "https://github.com/HenriquesLab/folder2md4llms/releases/download/v#{version}/folder2md-macos-x64"
      sha256 "INTEL_SHA256_TO_BE_UPDATED"
    else
      url "https://github.com/HenriquesLab/folder2md4llms/releases/download/v#{version}/folder2md-macos-arm64"
      sha256 "ARM64_SHA256_TO_BE_UPDATED"
    end
  end

  def install
    # Determine the correct binary name based on architecture
    if Hardware::CPU.intel?
      binary_name = "folder2md-macos-x64"
    else
      binary_name = "folder2md-macos-arm64"
    end

    # Install the binary
    bin.install binary_name => "folder2md"

    # Make sure it's executable
    chmod 0755, bin/"folder2md"
  end

  test do
    # Test version output
    version_output = shell_output("#{bin}/folder2md --version").strip
    assert_match version.to_s, version_output

    # Test help command
    help_output = shell_output("#{bin}/folder2md --help")
    assert_match "folder2md4llms converts", help_output

    # Test basic functionality
    (testpath/"test.py").write("print('hello world')")
    (testpath/"README.md").write("# Test Project")

    # Process the test directory
    system bin/"folder2md", testpath, "--output", "test.md"
    assert_path_exists testpath/"test.md"

    # Check that the output contains expected content
    output_content = File.read(testpath/"test.md")
    assert_match "test.py", output_content
    assert_match "README.md", output_content
    assert_match "Test Project", output_content

    # Test ignore file generation
    system bin/"folder2md", "--init-ignore"
    assert_path_exists testpath/".folder2md_ignore"

    # Verify ignore file has expected content
    ignore_content = File.read(testpath/".folder2md_ignore")
    assert_match "node_modules/", ignore_content
    assert_match "*.pyc", ignore_content
  end
end
