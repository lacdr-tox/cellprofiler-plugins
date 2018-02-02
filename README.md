# CellProfiler plugins

## Installation (conda)

Use the commands at top of `cp_environment.yml` to create conda environment. 
Make sure that it doesn't use packages from your `~/.local` python environment.

## Installation (old way)

1. When you start CellProfiler set the *CellProfiler plugins directory* to the `cp_plugins` directory, and the *ImageJ plugin directory* to the `ij_plugins` directory.
1. Set the `CLASSPATH` environment variable to include the jars `DImageSVN_.jar` and `jsch.jar` in the `jarlib` directory.
   There are various ways to set the classpath. For general instructions (Windows and Linux) see [here](https://docs.oracle.com/javase/tutorial/essential/environment/paths.html). 

   (Linux) Another way to set the classpath is on application basis like I did on the server in the `/usr/local/bin/cellprofiler` script:

   ```bash
   #!/bin/sh
   #
   # Wrapper script used to start CellProfiler on Linux.

   PREFIX=/opt/cellprofiler
   export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64
   export LD_LIBRARY_PATH=$JAVA_HOME/jre/lib/amd64/server
   export CLASSPATH=/data/shared/cellprofiler_plugins/jarlib/DImageSVN_.jar:/data/shared/cellprofiler_plugins/jarlib/jsch.jar
   python2 $PREFIX/CellProfiler/CellProfiler.py "$@"
   ```


3. (Linux) Make sure python-suds is available.

