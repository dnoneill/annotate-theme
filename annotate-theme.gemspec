# frozen_string_literal: true

Gem::Specification.new do |spec|
  spec.name          = "annotate-theme"
  spec.version       = "0.1.0"
  spec.authors       = [""]
  spec.email         = ["doneill@ncsu.edu"]

  spec.summary       = "Gem for annotate"
  spec.homepage      = "https://github.com/dnoneill/annotate"
  spec.license       = "MIT"

  spec.files = `git ls-files -z`.split("\x0").select do |f|
    f.match(%r{^(_(includes|layouts|sass)/|(LICENSE|README)((\.(txt|md|markdown)|$)))}i)
  end
  
  spec.add_runtime_dependency "jekyll", "~> 3.8"

  spec.add_development_dependency "bundler", "~> 2.2.10"
  spec.add_development_dependency "rake", "~> 12.0"
  spec.add_runtime_dependency 'jekyll-seo-tag', '~> 2.1'
  spec.add_runtime_dependency "rake", "~> 12.0"
end
