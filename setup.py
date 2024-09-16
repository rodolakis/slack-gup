from setuptools import setup, find_packages

setup(
    name='slackgup',
    author='Francesco De Carlo',
    author_email='decarlof@gmail.com',
    description='cli to create slack channel as GUP-# and share it with the users listed in the GUP',
    packages=find_packages(),
    entry_points={'console_scripts':['slack = slackgup.__main__:main'],},
    version=open('VERSION').read().strip(),
    zip_safe=False,
    url='https://github.com/xray-imaging/slackgup',
    download_url='https://github.com/xray-imaging/slack-gup.git',
    license='BSD-3',
    platforms='Any',
)