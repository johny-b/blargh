import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
     name='blargh',  
     version='0.0.1',
     author='Jan Betley',
     author_email='jan.betley@gmail.com',
     description='Generic REST API base',
     long_description=long_description,
     long_description_content_type='text/markdown',
     url='https://github.com/johny-b/blargh',
     packages=setuptools.find_packages(),
     install_requires=['psycopg2-binary', 'Flask', 'flask-restful'],
     classifiers=[
         'Programming Language :: Python :: 3',
         'Programming Language :: Python :: 3.7',
         'License :: OSI Approved :: MIT License',
     ],
 )
