from setuptools import setup

setup(
    name="todo",
    version="1.0",
    py_modules=["todo"],
    include_package_data=True,
    install_requires=["click", "GitPython"],
    entry_points="""
        [console_scripts]
        todo=todo:cli
    """,
)
