# Main script, it provides the user with a set of tool to automate local testing

import subprocess,os, platform, json, sys, time, datetime
try:
    assert sys.version_info >= (3,0)
except:
    print("You must have python 3.x installed on you computer to run this script")
    exit()
sys.path.insert(0, '../test')
from subprocess import DEVNULL, STDOUT, check_call
try:
    import unittests as tests
except:
    print("could not find unittests.py in ../test/")
    check = inputField('Continue ? (Y/N)')
    if check != 'Y':
        print("Cancelled")
        exit()
try:
    import docker
except ImportError:
    subprocess.check_call(["python", '-m', 'pip', 'install', 'docker']) 
    import docker
import logging

#prevents from having too much information on screen
logging.disable(logging.DEBUG)

dockerCli = docker.from_env()
validArgs = ["run", "test", "deploy", "help", "clean", "--cache", "--force", "config", "fromScript"]
options = ""
config = {}
runningOn = ""

if (platform.system() == "Windows"):
    print("Running on Windows")
    runningOn = "Windows"


args = {}
for x in range(2, len(sys.argv)):
    
    if sys.argv[x] not in validArgs:
        options = options + sys.argv[x] + " "
    else:
        args[sys.argv[x]] = True

appName = sys.argv[1]

if len(sys.argv) < 3:
    print("Bad arguments \n\n     Use : {} COMMAND [OPTIONS]".format(appName))
    exit()

def initConfig(): 
    conf = {
        'projectId':'project-123456789',
        'gcpRegion':'eu.gcr.io',
        'imageName':'image-name',
        'dockerVM':'default',
        'appAccessPort':'5000',
        'appContainerPort':'5000',
        'SQLRegion':'europe-west1',
        'SQLInstance':'app-sql',
        'deploymentName':'app-deployment',
        'gcpContainerName':'app-container'
    }
    return conf

def initApp():
    global config
    global ip
    try:
        json_data=open("config.json").read()
        config = json.loads(json_data)
    except:
        print("No configuration found!")
        config = initConfig()
        configApp()
        exit()

    if (runningOn == "Windows"):
        ip = ""
        try:
            ip = subprocess.check_output(["docker-machine", 'ip'])
        except:
            print("Docker is not running, starting docker-machine")
            try:
                subprocess.check_output(["docker-machine", 'restart', config["dockerVM"]])
            except:
                print("")
                exit()
        ip = subprocess.check_output(["docker-machine", 'ip']).decode("utf-8").rstrip() 
    return config

# Sets up variables
def configApp():
    def inputField(helpText, previousContent):
        tmp = input(helpText)
        if tmp == "":
            tmp = previousContent
        return tmp
    try:
        if (runningOn == "Windows"):
            config["dockerVM"] = inputField('Enter your docker virtual machine name (default : {}) : '.format(config["dockerVM"]), config["dockerVM"])

        config["projectId"] = inputField('Enter your gcp project id (default : {}) : '.format(config["projectId"]), config["projectId"])
        config["gcpRegion"] = inputField('Enter your gcp region (default : {}) : '.format(config["gcpRegion"]), config["gcpRegion"])
        config["imageName"] = inputField('Enter the docker image name to create (default : {}) : '.format(config["imageName"]), config["imageName"])
        config["appAccessPort"] = inputField('Enter the port to access your app (default : {}) : '.format(config["appAccessPort"]), config["appAccessPort"])
        config["appContainerPort"] = inputField('Enter the port exposed by the app container (default : {}) : '.format(config["appContainerPort"]), config["appContainerPort"])
        config["SQLInstance"] = inputField('Enter the name of your SQL instance (default : {}) : '.format(config["SQLInstance"]), config["SQLInstance"])
        config["SQLRegion"] = inputField('Enter the region of you SQL instance (default : {}) : '.format(config["SQLRegion"]), config["SQLRegion"])
        config["deploymentName"] = inputField('Enter the name of the deployment on Kubernetes (default : {}) : '.format(config["deploymentName"]), config["deploymentName"])
        config["gcpContainerName"] = inputField('Enter the application conainter name on Kubernetes (default : {}) : '.format(config["gcpContainerName"]), config["gcpContainerName"])
    except SyntaxError:
        print("Bad entry")
        exit()
    with open('config.json', 'w+') as outfile:
        json.dump(config, outfile)


def displayHelp():
    print("\nusage : {} COMMAND [OPTIONS]\n\n".format(appName))
    print("tool to manage {} excecution locally, testing and deployment to gcp host\n".format(appName))
    print("COMMANDS : \n")
    print("      clean : cleans system from untagged images and unused containers")
    print("      config : set up configuration such as ports and stuff")
    print("      deploy : deploys {} to Kubernetes".format(appName))
    print("      help : displays help")
    print("      run : runs {} in local mode with local config (such as PubSub and MySQL targets)".format(appName))
    print("      test : runs tests on {}".format(appName))
    print("\n\n")
    print("OPTIONS : \n")
    print("      --cache : uses a premade image for running {}".format(appName))
    print("      --force : skips test step while deploying")
    print("\n\n")
    print("TROUBLESHOOTING : \n")
    print("- make sure Google Sloud SDK is installed")
    print("- make sure kubectl is installed")
    print("- make sure you ran 'gcloud auth login'")
    print("- make sure you ran 'gcloud config' to set the right projectId and computeZone")
    print("- make sure you ran 'gcloud container clusters get-credential' with you cluster name")
    print("- make sure you ran 'gcloud auth configure-docker'")
    if (runningOn == "Windows"):
        print("- run docker-machine restart {}".format(config["dockerVM"]))
    print("\n\n")


# run the App container
def runApp():
    print("Checking availability on port {} ...".format(config["appAccessPort"]))
    runningContainers = dockerCli.containers.list(all=True, filters={'status':"running",'expose':"{}/tcp".format(config["appAccessPort"])})
    if len(runningContainers) > 0:
        try:
            print("Found container running {} on port {}".format(runningContainers[0].image.tags[0], config["appAccessPort"]))
        except:
            print("Found container on port {}".format(config["appAccessPort"]))
        print("Killing process")
        with open(os.devnull, 'w') as fp:
            #remove existing app window
            cmd = subprocess.Popen("taskkill /FI \"WindowTitle eq {}*\"".format(appName), stdout=fp)
            cmd.wait()
        print("Killing container ...")
        runningContainers[0].remove(force=True)
        print("Container killed")
    print("Building \"{}\" Docker image ...".format(config["imageName"]))
    proc = subprocess.Popen("docker build -t {} -f ../Dockerfile ..".format(config["imageName"]))
    proc.communicate()
    proc.wait()
    runContainer(config["appAccessPort"], config["appContainerPort"], config["imageName"], "--local", appName)
    print("{} started".format(appName))

# for dependencies, images might be based on dockerhub repos so we need to get them
def getImage(imageTag, repo):
    try:
        dockerCli.images.get(imageTag)
    except:
        print("[{}] not found locally".format(imageTag))
        if imageTag == "cloudsql:latest":
            #for cloudsql, credentials are required to access your google cloud sql database, so you need to provide a valid cred.json file containing the API key
            print("Creating Dockerfile.tmp for cloudsql:latest ...")
            f = open("Dockerfile.tmp", "w+")
            f.write("FROM antoinebillig/cloudsqlproxy\nCOPY cred.json ./\nENV GOOGLE_APPLICATION_CREDENTIALS cred.json\nENTRYPOINT [\"./cloud_sql_proxy\", \"-instances={}:{}:{}=tcp:0.0.0.0:3306\"]".format(config["projectId"],config["SQLRegion"],config["SQLInstance"]))
            f.close()
            print("Building image ...")
            with open(os.devnull, 'w') as fp:
                try:
                    proc = subprocess.Popen("docker build -t cloudsql:latest -f Dockerfile.tmp .")
                    proc.communicate()
                    proc.wait()
                except:
                    print("Error while building cloudsql image")
                    os.remove("Dockerfile.tmp")
                    exit()
            os.remove("Dockerfile.tmp")
            print("Image built successfully")

        else:
            print("Pulling [{}] from Dockerhub... ".format(imageTag))
            try:
                proc = subprocess.Popen("docker pull {}".format(repo))
                proc.communicate()
                proc.wait()
            except:
                print("Could not find {} image on Dockerhub".format(imageTag))
                exit()
            print("Image pulled!")
            pubsubImg = dockerCli.images.get(repo)
            #tagging image with desired tag instead of repo name
            print("Tagging image")
            pubsubImg.tag(imageTag)
            print("Image tagged")


# Helper to run a container. It returns when the container has a 'running' status.
def runContainer(appPort, containerPort, image, imageOptions, containerName):
    print("Starting new container ...")
    os.popen("Start \"{}\" cmd /c cmd /k docker run -p {}:{} {} {}".format(containerName, appPort,containerPort,image, imageOptions))
    print("Waiting for {} to start ...".format(containerName))
    while True:
        runningContainers = dockerCli.containers.list(all=True, filters={'status':"running",'expose':"{}/tcp".format(appPort)})
        if runningContainers != []:
            break
        time.sleep(1) 

# Helper to set up and launch a container. It kills and remove currently running container on a given port then starts the new container.
def startContainer(containerName, appPort, containerPort, imageTag, repo, appOptions, replace = False):
    print("Checking {} on port {} ...".format(containerName, appPort))
    runningContainers = dockerCli.containers.list(all=True, filters={'status':"running",'expose':"{}/tcp".format(appPort)})
    for i in range(0, len(runningContainers)):
        containerFound = False
        for j in range(0, len(runningContainers[i].image.tags)):
            if runningContainers[i].image.tags[j] == imageTag:
                containerFound = True
        if not containerFound or replace:
            if not replace:
                print("An container is already running on port {} and is not detected being a {} image".format(appPort, containerName))
            print("Killing process")
            with open(os.devnull, 'w') as fp:
                cmd = subprocess.Popen("taskkill /FI \"WindowTitle eq {}*\"".format(containerName), stdout=fp)
                cmd.wait()
            print("Killing container ...")
            runningContainers[0].remove(force=True)
            print("Container killed")
            getImage(imageTag, repo)
            runContainer(appPort, containerPort, imageTag, appOptions, containerName)
    if len(runningContainers) == 0:
        getImage(imageTag, repo)
        runContainer(appPort, containerPort, imageTag, appOptions, containerName)
    print("{} is running".format(containerName))

# Helper to run app dependencies 
def runDependencies(replace = False):
    startContainer("PubSub", "8085", "8085", "pubsub_sim:latest", "antoinebillig/pubsub_sim", "", replace)
    startContainer("CloudSQL", "3306", "3306", "cloudsql:latest", "antoinebillig/cloudsqlproxy", "", replace)

# Helper to run the user defined scripts. The test file should return 'KO' when failing, everything else will be considered as OK
def runTests():
    print("Testing {}".format(appName))
    testRes = tests.main(["../test/unittests.py"])

    if testRes == "KO":
        print("Tests failed")
        exit()
    else:
        print("Tests succeeded")

# Function to manually update an existing deployment on kubernetes.
# It first create a tag that include the gcp container registery URL as well as the image name followed by the key word manual for identification as well as a timestamp for the tag.
def deployApp():
    print("Deploying {} to Kubernetes ...".format(appName))
    date = datetime.datetime.today()
    timeStamp = "{:02d}{:02d}{:02d}{:02d}{:02d}".format(date.month, date.day, date.hour, date.minute,date.second)
    imageTag = "t{}".format(timeStamp)
    imageName = "{}/{}/{}manual".format(config["gcpRegion"], config["projectId"], config["imageName"])
    pubsubImg = dockerCli.images.get("{}:latest".format(config["imageName"]))
    pubsubImg.tag("{}:{}".format(imageName, imageTag))
    proc = subprocess.Popen("docker push {}:{}".format(imageName, imageTag))
    proc.communicate()
    proc.wait()
    proc = subprocess.Popen("kubectl set image deployment {} {}={}:{}".format(config["deploymentName"], config["gcpContainerName"], imageName, imageTag))
    proc.communicate()
    proc.wait()

# Helper to clean unused images and containers, as well as deployment images
def cleanSystem():
    containers = dockerCli.containers.list()
    for container in containers:
        container.remove(force=True)
    dockerCli.containers.prune()
    dockerCli.images.prune()
    images = dockerCli.images.list()
    appImages = "{}/{}/{}manual".format(config["gcpRegion"], config["projectId"], config["imageName"]) 
    for image in images:
        if len(image.tags) > 0 and appImages in image.tags[0]:  
            dockerCli.images.remove(image=image.id, force=True)
    print("Success")


initApp()

if "fromScript" not in args:
    print("please launch this script from the script file (*.sh/*.bat)")
    exit()

elif "--cache" in args:
    print("option not available at the moment")
    exit()

elif "config" in args:
    configApp()
    exit()

elif "clean" in args:
    cleanSystem()
    exit()

elif "test" in args:
    runDependencies(True)
    runApp()
    runTests()
    if (runningOn == "Windows"):
        print("\n{} base URL : {}:{}".format(appName, ip, config["appAccessPort"]))
    exit()

elif "deploy" in args:
    if "--force" in args:
        pass
    else:
        runDependencies(True)
        runApp()
        runTests()
    deployApp()
    exit()

elif "run" in args:
    runDependencies(True)
    runApp()
    if (runningOn == "Windows"):
        print("\n{} base URL : {}:{}".format(appName, ip, config["appAccessPort"]))
    exit()
    
else:
    displayHelp()
    exit()
