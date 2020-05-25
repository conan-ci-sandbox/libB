from conans import ConanFile, CMake

class LibB(ConanFile):
    name = "libB"
    version = "1.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = {"shared": False}

    generators = "cmake"

    scm = {"type": "git",
           "url": "/var/lib/jenkins/git_server/libB.git",
           "revision": "auto"}

    def requirements(self):
        self.requires("libA/1.0@mycompany/stable")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        cmake.install()

    def package(self):
        self.copy("LICENSE", dst="licenses")

    def package_info(self):
        self.cpp_info.libs = ["libB",]
