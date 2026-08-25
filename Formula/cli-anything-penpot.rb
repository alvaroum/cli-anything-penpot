class CliAnythingPenpot < Formula
  desc "Lightweight, agent-friendly CLI for the Penpot HTTP API"
  homepage "https://github.com/alvaroum/cli-anything-penpot"
  url "https://github.com/alvaroum/cli-anything-penpot/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "85b14032db31bf54f2454a9dedaa45c22ac103af4f29b3880ed592ec3d3f633a"
  license "MIT"

  resource "click" do
    url "https://files.pythonhosted.org/packages/ae/44/c1221527f6a71a01ec6fbad7fa78f1d50dfa02217385cf0fa3eec7087d59/click-8.3.3-py3-none-any.whl"
    sha256 "a2bf429bb3033c89fa4936ffb35d5cb471e3719e1f3c8a7c3fff0b8314305613"
  end

  depends_on "python@3.13"

  def install
    virtualenv_create(libexec, "python3")
    resource("click").stage do
      system libexec/"bin/pip", "install", "--no-index", Dir["*.whl"].first
    end
    system libexec/"bin/pip", "install", "--no-deps", "."
    bin.install_symlink libexec/"bin/cli-anything-penpot"
    bin.install_symlink libexec/"bin/penpot"
  end

  test do
    assert_match "Control Penpot", shell_output("#{bin}/cli-anything-penpot --help")
    assert_match "0.1.0", shell_output("#{bin}/cli-anything-penpot --version")
  end
end
