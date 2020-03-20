from setuptools import setup

setup(
    name='git-tools',
    version='0.1',
    py_modules=['feature'],
    install_requires=[
        'Click',
        'sh',
    ],
    entry_points='''
        [console_scripts]
        git-feature=feature:feature
        git-finish=feature:finish
    ''',
)
