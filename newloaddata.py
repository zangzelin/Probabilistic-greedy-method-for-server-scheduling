from util import *
import numpy as np
from functools import reduce

global zzl_solution_file_a
Joblist = []

def ReadAppResources(app_resources_file):
    # app resource
    app_resfile = open(app_resources_file)
    for line in app_resfile:
        line = line.strip('\n')
        vec_resource = line.split(',')
        appid = vec_resource[0]
        cpu = np.array(vec_resource[1].split('|'))
        cpu = cpu.astype(np.float)
        mem = np.array(vec_resource[2].split('|'))
        mem = mem.astype(np.float)
        disk = float(vec_resource[3])
        P = int(vec_resource[4])
        M = int(vec_resource[5])
        PM = int(vec_resource[6])
        app = App(appid, cpu, mem, disk, P, M, PM)
        Apps[appid] = app


def ReadJobInformation(job_info_file_a):
    # app resource
    app_resfile = open(job_info_file_a)
    for line in app_resfile:
        line = line.strip('\n')
        part1, part2 = line.split('|')

        vec_resource = part1.split(',')
        job_id = vec_resource[0]
        cpu = float(vec_resource[1])
        mem = float(vec_resource[2])
        number_of_instances = int(vec_resource[3])
        execution_time = int(vec_resource[4])
        dependency_task_id = vec_resource[5:-1]

        starttime, endtime = part2.split(',')
        starttime = int(starttime)
        endtime = int(endtime)

        job = Job(job_id, cpu, mem, number_of_instances,
                  execution_time, dependency_task_id, starttime, endtime)
        Joblist.append(job_id)
        Jobs[job_id] = job


def ReadMachineResources(machine_resources_file_a):
    # machine resource
    machine_resfile = open(machine_resources_file_a)
    for line in machine_resfile:
        line = line.strip('\n')
        vec_resource = line.split(',')
        machineid = vec_resource[0]
        cpu = np.array(vec_resource[1].split('|'))
        cpu = cpu.astype(np.float)
        mem = np.array(vec_resource[2].split('|'))
        mem = mem.astype(np.float)
        disk = int(vec_resource[3])
        P = int(vec_resource[4])
        M = int(vec_resource[5])
        PM = int(vec_resource[6])
        machine = Machine(machineid, cpu, mem, disk, P, M, PM)
        Machines[machineid] = machine


def ReadInferrence(app_interference_file):
    # machine resource
    inferrence_file = open(app_interference_file)
    for line in inferrence_file:
        line = line.strip('\n')
        vec_resource = line.split(',')
        appa = vec_resource[0]
        appb = vec_resource[1]
        k = int(vec_resource[2])
        Inferrences[appa+" "+appb] = k
        # Inferrences[appb+" "+appa] = k


def ReadDeploy(inst_deploy_file_a):
    # 读取Inst部署的情况
    # 全局变量表示已提前部署的inst
    PreDeploy
    # 全局变量表示未提前部署的inst
    NonDeploy
    deploy_file = open(inst_deploy_file_a)
    for line in deploy_file:
        line = line.strip('\n')
        vec_resource = line.split(',')
        inst = vec_resource[0]
        app = vec_resource[1]
        machine = vec_resource[2]

        if(len(machine) > 1):
            PreDeploy.append([inst, app, machine])
        else:
            NonDeploy.append([inst, app, ''])
        Insts[inst] = [app, None]
        Apps[app].instance.append(inst)


def CheckConstraint():
    for machine in Deployments:
        # print(machine)
        localInsts = Deployments[machine]
        AppCounter = {}
        if not len(localInsts):
            continue
        # check cpu
        localCpu = np.zeros((98,), dtype=np.float)
        # check memory
        localMem = np.zeros((98,), dtype=np.float)
        # check disk
        localDisk = 0
        # check P
        localP = 0
        # check M
        localM = 0
        # check PM
        localPM = 0
        for inst in localInsts:
            localCpu += Apps[Insts[inst][0]].cpu
            localMem += Apps[Insts[inst][0]].mem
            localDisk += Apps[Insts[inst][0]].disk
            localP += Apps[Insts[inst][0]].P
            localM += Apps[Insts[inst][0]].M
            localPM += Apps[Insts[inst][0]].PM

        # check  cpu
        compare = np.greater_equal(Machines[machine].cpu, localCpu)
        # print(compare)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            logger.debug("CPU fail on "+machine)
            return False
            # check  mem

        compare = np.greater_equal(Machines[machine].mem, localMem)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            logger.debug("Memory fail on "+machine)
            return False

        # check  disk
        compare = Machines[machine].disk >= localDisk
        if(not compare):
            logger.debug("disk fail on "+machine)
            return False

        # check  P
        compare = Machines[machine].P >= localP
        if(not compare):
            logger.debug("P fail on "+machine)
            return False

        # check  M
        compare = Machines[machine].M >= localM
        if(not compare):
            ("M fail on "+machine)
            return False

        # check  PM
        compare = Machines[machine].PM >= localPM
        if(not compare):
            logger.debug("PM fail on "+machine)
            return False

        # check inferrence
        for inst in localInsts:
            curApp = Insts[inst][0]
            if curApp not in AppCounter:
                AppCounter[curApp] = 1
            else:
                AppCounter[curApp] += 1

        for appa in curApp:
            for appb in curApp:
                if appa+" "+appb in Inferrences:
                    if AppCounter[appb] > Inferrences[appa+" "+appb]:
                        print("Inferrence between "+appa+" " +
                              appb+" broken "+"on "+machine)
                        return False
        # constraint satisfy
    return True


def Loaddata(text):
    if text == 'olda':
        olddata_app_interference_file = 'data/olddata/scheduling_preliminary_app_interference_20180606.csv'
        olddata_app_resources_file = 'data/olddata/scheduling_preliminary_app_resources_20180606.csv'
        olddata_machine_resources = 'data/olddata/scheduling_preliminary_machine_resources_20180606.csv'
        olddata_inst_deploy_file = 'data/olddata/scheduling_preliminary_instance_deploy_20180606.csv'
        zzl_solution_file_a = "./submit/solution_olda.csv"

        sort_ins_list = np.loadtxt('inssort/sort' + text + '.txt')
        ReadAppResources(olddata_app_resources_file)
        ReadMachineResources(olddata_machine_resources)
        ReadInferrence(olddata_app_interference_file)
        ReadDeploy(olddata_inst_deploy_file)

    if text == 'oldb':
        olddata_app_interference_file = 'data/olddata/scheduling_preliminary_b_app_interference_20180726.csv'
        olddata_app_resources_file = 'data/olddata/scheduling_preliminary_b_app_resources_20180726.csv'
        olddata_machine_resources = 'data/olddata/scheduling_preliminary_b_machine_resources_20180726.csv'
        olddata_inst_deploy_file = 'data/olddata/scheduling_preliminary_b_instance_deploy_20180726.csv'
        zzl_solution_file_a = "./submit/solution_oldb.csv"

        sort_ins_list = np.loadtxt('inssort/sort' + text + '.txt')
        ReadAppResources(olddata_app_resources_file)
        ReadMachineResources(olddata_machine_resources)
        ReadInferrence(olddata_app_interference_file)
        ReadDeploy(olddata_inst_deploy_file)
        # ReadJobInformation()

    if len(text) == 1:
        data_app_interference_file = "./data/app_interference.csv"
        data_app_resources_file = "./data/app_resources.csv"
        data_machine_resources = "./data/machine_resources."+text+".csv"
        data_inst_deploy_file = "./data/instance_deploy."+text+".csv"
        job_info_file_a = "outlineJobSort/time_"+text.upper()+"_job.csv"
        zzl_solution_file_a = "./submit/solution"+text+".csv"

        sort_ins_list = np.loadtxt('inssort/sort' + text + '.txt')
        ReadAppResources(data_app_resources_file)
        ReadMachineResources(data_machine_resources)
        ReadInferrence(data_app_interference_file)
        ReadDeploy(data_inst_deploy_file)
        ReadJobInformation(job_info_file_a)

    return sort_ins_list
