#!/usr/bin/env python3

#
#  Copyright (C) 2019-2020  XC Software (Shenzhen) Ltd.
#

import argparse
import logging
import sys
import time
import json

from common import CommonGlobals
from common.XcalException import XcalException
from common.CommonGlobals import TaskErrorNo
from common.ConfigObject import ConfigObject
from XcalGlobals import *


from common.XcalLogger import XcalLogger
from components.XcalConnect import Connector
from components.XcalTasks import TaskRunner


PREPROCESS_FILE_NAME = "preprocess.tar.gz"  # preprocessed file package name
FILE_INFO_FILE_NAME = "fileinfo.json"       # file info's file name
SOURCE_CODE_ARCHIVE_FILE_NAME = "source_code.zip"
SOURCE_FILES_NAME = "source_files.json"
BASE_SCAN_PATH = "/share/scan/"


def get_parser():
    parser = argparse.ArgumentParser(description = 'xcal scanner, do preprocess and drive the whole scan process')

    parser.add_argument('--scanner-conf', '-sc', dest = 'scanner_conf', type = argparse.FileType('r'),
                        metavar = 'xcal-scanner.conf', required = False, help = "scanner config file")
    parser.add_argument('--project-conf', '-pc', dest = 'project_conf', type = argparse.FileType('r'),
                        metavar = 'xcal-project.conf', required = False, help = 'project config file')
    parser.add_argument('--project-id', '-pid', dest = 'project_id', required = False,
                        help = 'the unique id of the project')
    parser.add_argument('--project-name', '-pname', dest = 'project_name', required = False,
                        help = 'the project name of the project, will display on UI')
    parser.add_argument('--project-path', '-ppath', dest = 'project_path', required = False,
                        help = 'project source code path')
    parser.add_argument('--build-path', '-bpath', dest = 'build_path', required = False,
                        help = 'project build path')
    parser.add_argument('--build-command', '-bc', dest = 'build_command', required = False, default = 'make',
                        help = 'default value is make')     # not used yet
    parser.add_argument('--server-url', '-surl', dest = 'server_url', required = False,
                        help = 'server url, for example: http://host:port')
    parser.add_argument('--new-project', '-np', dest = 'new_project', action = 'store_true',
                        help = 'indicate this is a new project')
    parser.add_argument('--upload-source-code', '-usc', dest = 'upload_source_code', action = 'store_true',
                        help = 'upload source code to server')
    parser.add_argument('--debug', '-d', dest = 'debug', action = 'store_true',
                        help = 'enable debug mode')

    return parser


def process_arguments(arguments, global_ctx):
    """
    parse all the command line options, fill it into a dict object. update global_ctx
    command line option may override the value which filled in the conf file
    :param arguments:
    :return: a dict object, and updated global_ctx
    """
    logging.info("process_arguments: begin to process arguments")

    arguments_dict = dict()
    arguments_dict['newProject'] = arguments.new_project
    arguments_dict['uploadSourceCode'] = arguments.upload_source_code

    if arguments.scanner_conf is not None:
        logging.debug(arguments.scanner_conf)
        global_ctx = ConfigObject.merge_two_dicts(global_ctx, json.load(arguments.scanner_conf))

    if arguments.project_conf is not None:      # if not provided, find the project path for the xcal-project.conf
        logging.debug(arguments.project_conf)
        arguments_dict = ConfigObject.merge_two_dicts(arguments_dict, json.load(arguments.project_conf))

    # if arguments.server_url is not None:
        # arguments_dict.get("apiServer").get("host") = arguments.server_url

    if arguments.project_id is not None:
        arguments_dict['projectId'] = arguments.project_id

    if arguments.project_path is not None:
        arguments_dict['projectPath'] = arguments.project_path

    # Make sure buildPath is set
    if arguments.build_path is not None:
        arguments_dict['buildPath'] = arguments.build_path
    elif arguments_dict.get("buildPath") is None:
        # If user provides neither arguments.build_path or arguments_dict.get("buildPath"), we will use projectPath instead.
        arguments_dict['buildPath'] = arguments_dict.get('projectPath')

    if arguments_dict.get('projectId') is None or arguments_dict.get('projectPath') is None or arguments_dict.get('buildPath') is None:
        logging.error("project id, project path, build path must be provided")
        sys.exit(1)

    return arguments_dict, global_ctx


def get_not_none(storage_obj, key):
    if storage_obj.get(key) is None:
        raise XcalException("xcal-scanner", "get_not_non", "key %s not found" % key, TaskErrorNo.E_KEY_NOT_FOUND)
    return storage_obj.get(key)


def prepare_job(project_info, global_ctx, arguments_dict, scan_task_id:str, project_id:str):
    logging.info("prepare_job: begin to prepare the job steps")
    logging.debug("project_info: %s, arguments_dict: %s" % (project_info, arguments_dict))

    project_config = json.loads(project_info.get("projectConfig"))
    scan_config = json.loads(project_info.get("scanConfig"))

    task_config = dict()
    task_config["sourceStorageName"] = "agent"  # hard code here
    task_config["sourceStorageType"] = "agent"      # hard code here
    if arguments_dict.get("uploadSourceCode"):
        task_config["uploadSource"] = "Y"
    else:
        task_config["uploadSource"] = "N"

    task_config["scanFilePath"] = os.path.join(BASE_SCAN_PATH, scan_task_id)
    task_config["sourceCodePath"] = project_config.get("relativeSourcePath")
    task_config["preprocessPath"] = project_config.get("relativeBuildPath")
    task_config["configContent"] = scan_config
    task_config["projectId"] = project_id
    task_config["scanTaskId"] = scan_task_id
    task_config["token"] = global_ctx.get('agentToken')

    job_config = dict()
    job_config["agentType"] = 'offline_agent'   # hard code here
    job_config["taskConfig"] = task_config

    steps = []

    user_config = job_config.get("taskConfig").get("configContent")
    preprocess_location = job_config.get("taskConfig").get("preprocessPath")

    upload_source = False
    if task_config.get("uploadSource") is not None and str(task_config.get("uploadSource")) == "Y":
        upload_source = True

    if job_config.get("sourceCodeAddress") is not None:
        # source code url
        timeout = "1200"
        if job_config.get("timeout") is not None:
            timeout = job_config.get("timeout")
        # Add Source Code Fetch Task
        steps.append({"id": len(steps), "parent": 0, "type": "getSourceCode",
                      "sourceCodeAddress": job_config.get("sourceCodeAddress"), "timeout": timeout})
    elif job_config.get("sourceCodeFileId") is not None:
        # source code file id
        timeout = "1200"
        if job_config.get("timeout") is not None:
            timeout = job_config.get("timeout")
        # Add Source Code Fetch Task
        steps.append({"id": len(steps), "parent": 0, "type": "downloadSourceCode",
                      "sourceCodeFileId": job_config.get("sourceCodeFileId"), "timeout": timeout})

    # source_storage_name and source_storage_type is related to the fileStorage information in web service
    source_storage_name = task_config.get("sourceStorageName", "agent").lower()
    source_storage_type = task_config.get("sourceStorageType", "agent").lower()
    source_code_file_id = ""
    gitlab_project_id = ""
    git_url = ""

    if source_storage_type == "volume" and source_storage_name == "volume_upload":
        source_code_file_id = get_not_none(job_config, "sourceCodeFileId")
    elif source_storage_type == "gitlab":
        git_url = get_not_none(job_config, "sourceCodeAddress")
        gitlab_project_id = get_not_none(job_config, "gitlabProjectId")
    elif source_storage_type == "github":
        git_url = get_not_none(job_config, "sourceCodeAddress")

    source_location = task_config.get("sourceCodePath", "/")
    logging.debug("User specified source Code location: %s" % source_location)

    # Prepare the steps list

    if user_config.get("lang") == "java":
        # Java -> Plugin
        java_command = user_config.get("build", "mvn")
        java_command_option = user_config.get("buildConfig", "")

        # Maven/Gradle Plugin invocation
        steps.append(
            {"id": len(steps), "parent": 0, "type": "java", "sourceStorageName": source_storage_name,
             "workdir": preprocess_location, "outputDir": preprocess_location,
             "buildMainDir": preprocess_location,
             "buildCommand": java_command, "buildConfig": java_command_option})

        # Runtime.o generation
        steps.append(
            {"id": len(steps), "parent": 0, "type": "runtimeObjectCollect", "sourceStorageName": source_storage_name,
             "workdir": preprocess_location, "outputDir": preprocess_location,
             "name": "runtimeObjectCollect"})

        # Scanner Connector / Spotbugs
        steps.append(
            {"id": len(steps), "parent": 0, "type": "scannerConnector", "sourceStorageName": source_storage_name,
             "workdir": preprocess_location, "outputDir": preprocess_location,
             "buildMainDir": preprocess_location,
             "name": "scannerConnector"})
    else:
        # C/C++ -> XcalBuild

        # Prebuild (This is a back stage operation, not used right now)
        if user_config.get("prebuild") is not None:
            steps.append(
                {"id": len(steps), "parent": 0, "type": "command", "sourceStorageName": source_storage_name,
                 "workdir": preprocess_location,
                 "cmd": user_config.get("prebuild")})

        build_cmd = user_config.get("buildCommand", "make")

        # Add XcalBuild Step
        xcalbuild_step = \
            {"id": len(steps), "parent": 0, "type": "xcalbuild", "sourceStorageName": source_storage_name,
             "buildMainDir": preprocess_location,
             "buildCommand": build_cmd}

        # If configureCommand exists, add it to the xcalbuild step
        if user_config.get('configureCommand') is not None:
            xcalbuild_step["configureCommand"] = user_config.get('configureCommand')

        # XcalBuild Preprocess
        steps.append(xcalbuild_step)

    # If user choose to upload source code on Agent Mode, add upload step
    if upload_source:
        timeout = "1200"
        if job_config.get("timeout") is not None:
            timeout = job_config.get("timeout")
        steps.append(
            {"id": len(steps), "parent": 0, "type": "compressSourceCode", "sourceStorageName": source_storage_name,
             "sourceCodePath": task_config.get("sourceCodePath"),
             "outputFileName": SOURCE_CODE_ARCHIVE_FILE_NAME, "inputFileName": SOURCE_FILES_NAME,
             "timeout": timeout})
        steps.append(
            {"id": len(steps), "parent": 0, "type": "upload", "sourceStorageName": source_storage_name,
             "filename": SOURCE_CODE_ARCHIVE_FILE_NAME, "name": "sourceCode"})

    # Prepare FileInfo
    steps.append(
        {"id": len(steps), "parent": 0, "type": "prepareFileInfo", "sourceStorageName": source_storage_name,
         "sourceStorageType": source_storage_type, "uploadSource": upload_source,
         "srcDir": source_location, "outputFileName": FILE_INFO_FILE_NAME, "inputFileName": SOURCE_FILES_NAME,
         "sourceCodeFileId": source_code_file_id, "gitlabProjectId": gitlab_project_id, "gitUrl": git_url,
         "sourceCodeArchiveName": SOURCE_CODE_ARCHIVE_FILE_NAME})

    # Upload FileInfo
    steps.append({"id": len(steps), "parent": 0, "type": "upload", "sourceStorageName": source_storage_name,
                  "filename": FILE_INFO_FILE_NAME, "name": "fileInfo"})

    # Upload Preprocess Results
    steps.append({"id": len(steps), "parent": 0, "type": "upload", "sourceStorageName": source_storage_name,
                  "filename": PREPROCESS_FILE_NAME, "name": "preprocessResult"})

    # Perform Cleanup
    steps.append({"id": len(steps), "parent": 0, "type": "sourceCleanup"})

    job_config["steps"] = steps
    return job_config


# login failed will terminate xcal-scanner.py program not matter what reason
def get_token(global_ctx, log: XcalLogger):
    login_response = Connector(log, global_ctx.get("apiServer")).login(global_ctx)
    if 400 <= login_response.status_code < 500:
        log.warn("get_token", "failed, please check whether username/password is incorrect")
        sys.exit(1)
    elif 500 <= login_response.status_code < 600:
        log.warn("get_token", "failed, please check whether the server is available")
        sys.exit(1)
    else:
        return login_response.json().get("accessToken")


def command_line_runner():
    start = time.time()

    parser = get_parser()
    arguments = parser.parse_args()
    
    global_ctx = DEFAULT_CONFIG.copy()
    global_ctx["xcalAgentInstallDir"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    arguments_dict, global_ctx = process_arguments(arguments, global_ctx)

    if arguments.debug is True:
        CommonGlobals.log_level = logging.DEBUG
        logging.getLogger().setLevel(CommonGlobals.log_level)
        
    elif global_ctx.get("logLevel") is not None:
        conf_level = global_ctx.get("logLevel")
        if conf_level == "DEBUG":
            CommonGlobals.log_level = logging.DEBUG
        elif conf_level == "INFO":
            CommonGlobals.log_level = logging.INFO
        elif conf_level == "TRACE":
            CommonGlobals.log_level = XcalLogger.XCAL_TRACE_LEVEL
        elif conf_level == "WARN":
            CommonGlobals.log_level = logging.WARN
        elif conf_level == "ERROR":
            CommonGlobals.log_level = logging.ERROR
        else:
            CommonGlobals.log_level = logging.WARNING
        logging.getLogger().setLevel(CommonGlobals.log_level)

    CommonGlobals.use_jaeger = False    # disable use jaeger

    # create project, get project config, add scan task
    # prepare_job get the job_config object which will be used to drive the preprocess/scan task
    with XcalLogger("xcal-scanner.py", "command_line_runner", real_tracer = False) as log:
        try:
            log.trace("command_line_runner", " trying to login to server ...")
            global_ctx["agentToken"] = get_token(global_ctx, log)
            log.trace("command_line_runner", " login completed.")

            connector = Connector(log, global_ctx.get("apiServer"))
            if arguments_dict.get("newProject"):
                log.trace("command_line_runner", " creating project as newProject is marked ...")
                log.info("command_line_runner", " sending to api: %s" % json.dumps(arguments_dict))
                project_obj = connector.create_project(global_ctx, arguments_dict)
                logging.debug("command_line_runner, project_obj: %s" % project_obj.json())
                log.trace("command_line_runner", " project created.")
            
            project_config_obj = connector.get_project_config(global_ctx, arguments_dict.get("projectId")).json()
            logging.debug("command_line_runner, project_config_obj: %s" % project_config_obj)
            
            log.trace("command_line_runner", " creating project scan task ...")
            scan_task_obj = connector.add_scan_task(global_ctx, project_config_obj.get("project").get("id")).json()
            logging.debug("command_line_runner, scan_task_obj: %s" % scan_task_obj)

            log.trace("command_line_runner", " preparing the job configuration ...")
            job_config = prepare_job(project_config_obj, global_ctx, arguments_dict, scan_task_obj.get("id"), project_config_obj.get("project").get("projectId"))
            
        except (AttributeError, json.JSONDecodeError) as err:
            logging.error(err)
            sys.exit(1)
        except XcalException as err:
            logging.error(err.message)
            sys.exit(1)
        log.trace("command_line_runner", " performing offline preprocessing ...")  
        # here True means after preprocess is done, call scan service do scan
        job_config = TaskRunner(log, global_ctx).perform_offline_tasks(global_ctx, job_config, log, True)
        log.trace("command_line_runner", " offline preprocessing finished.")
        # need to call update status and indicate preprocess is ok?
        # begin to call scan start api.
        # Connector(log).call_scan_service(global_ctx, job_config)

    end = time.time()
    logging.info("------------------------------------------------------------------------")
    logging.info("EXECUTION SUCCESS")
    logging.info("------------------------------------------------------------------------")
    logging.info("Total time: %ss" % (end - start))
    logging.info("------------------------------------------------------------------------")
    return


if __name__ == "__main__":
    work_dir = os.path.abspath(os.curdir)
    logging.getLogger('').handlers = []
    logFormatter = '[%(asctime)20s] [%(levelname)10s] [%(threadName)s] %(message)s'
    logging.basicConfig(format=logFormatter, level=CommonGlobals.log_level)
    logging.addLevelName(XcalLogger.XCAL_TRACE_LEVEL, "TRACE")

    rootLogger = logging.getLogger()
    fileHandler = logging.FileHandler(os.path.join(work_dir, AGENT_LOG_FILE_NAME))
    fileHandler.setFormatter(logging.Formatter(logFormatter))
    rootLogger.addHandler(fileHandler)
    command_line_runner()

# TODO: maybe can update the projectConfig in web server? Add another parameter to indicate this?
# TODO: add a parameter to print the log message to a specified file?
