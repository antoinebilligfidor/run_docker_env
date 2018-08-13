# run_docker_env
Some little tools to automate docker set up and execution on your local machine


**For the moment it is only working for Windows hosts.**


The script will allow you to fully automate some commands such as docker run , docker kill, docker rm that you would usually have to do and sometimes custom (ports binding etc). It is especially usefull to automatically free a port when you want to re run a container.
Also it can run an app with its dependencies. So far, it is configured to run a pubsub local emulator as well as a google cloud mysql proxy.


***To set it up, just change the batch file name to something that matches your project name. You might also want to change the last line of that same script to something that makes more sense than 'App'.***


To be able to run any commands, you must have installed and configured Google Cloud SDK and kubectl. (gcloud auth login/ gcloud config for project ID and zone/ gcloud container cluster get-credentials for the right cluster). Also you need run gcloud auth configure-docker to allow push to Google Cloud Registry.
If you were to use the CloudSQL proxy, you also need an existing mysql database on Google Cloud SQL and the related infos (region/instance name)

Then just call the script (here with app):
'app run '
it should ask you for some configuration information the first time you run it. (you can latter edit those with 'app config')
If the set up is done correctly, you should have the dependencies starting, then your app image built and executed.


**Here is a list of the available commands :**

* 'run' : for running the app, so that you can check the behavior, such as API fonctions.
* 'test' : for running the app and run the unit tests you specified in a folder test at the parent level.
* 'config' : for editing the current configuration.
* 'clean' : for removing unused images and containers , as well as temporary images created with the script.
* 'deploy' : for running/testing/deploying the app to kubernetes. 
* '--force' : to force the deploy and skip testing step.


