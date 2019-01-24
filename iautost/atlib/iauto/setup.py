from setuptools import setup, find_packages

setup(
      name="autost",
      version="0.10",
      description="automatic system test for iauto.",
      author="liuxinxing",
      url="http://www.baidu.com",
      license="Commercial",
      packages=find_packages(),
      #scripts=["scripts/autost.py"],
      #package_data={"": ["*.dll", "*.exe", "adb*", "*.html"]},
      include_package_data=True,
      exclude_package_data={"":[".gitignore", "*.pyc", "*.log"]},
      zip_safe=False,
      )