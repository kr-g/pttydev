import setuptools

with open("README.MD", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pttydev", 
    version="v0.0.3",
    author="k.r. goger",
    author_email="k.r.goger+pttydev@gmail.com",
    description="TTYDev - Pseudo TTY Device",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kr-g/pttydev",
    packages=setuptools.find_packages(),
    license = 'MIT',
    keywords = 'python threading pyserial websocket websocket-client micropython webrepl esp8266 esp32',
    install_requires=['pyatomic','pyserial','websocket-client',],    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: POSIX :: Linux',
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.6',
)

