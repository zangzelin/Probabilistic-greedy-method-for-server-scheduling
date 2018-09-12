import logging
import logging.handlers
import random
from functools import reduce
from math import exp, expm1
import matplotlib.pyplot as plt

import numpy as np

# log file
LOG_FILE = './log/log1.log'
handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=1024*1024, backupCount=5)  # 实例化handler
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'

formatter = logging.Formatter(fmt)   # formatter
handler.setFormatter(formatter)

logger = logging.getLogger('log')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Global variable, APP stores the object of the APP,
# the key is the id of the app,
# and the value is the instance of the APP object.
Apps = {}

# Global variables store each machine class key is the machine id,
# value is the machine object instance
Machines = {}
CutMachines = []

Jobs = {}

Tasks = {}
# Global Variables The Inferrence key between each app is appa+' 'appb,
# value is the constraint value
Inferrences = {}

# Global variables store each Insts instance class
Insts = {}

# The global variable stores the current deployment status.
# The key is the inst id,
# the value is the binary group [appid, machine_id],
# the app_id represents the corresponding app number,
# and the machine_id is empty.
Deployments = {}

# Global variables indicate insts that have been deployed in advance
PreDeploy = []

# Global variables indicate insts that are not deployed in advance
NonDeploy = []

# input file name
app_resources_file = "./data/app_resources.csv"
app_interference_file = "./data/app_interference.csv"

inst_deploy_file_a = "./data/instance_deploy.a.csv"
inst_deploy_file_b = "./data/instance_deploy.b.csv"
inst_deploy_file_c = "./data/instance_deploy.c.csv"
inst_deploy_file_d = "./data/instance_deploy.d.csv"
inst_deploy_file_e = "./data/instance_deploy.e.csv"

machine_resources_file_a = "./data/machine_resources.a.csv"
machine_resources_file_b = "./data/machine_resources.b.csv"
machine_resources_file_c = "./data/machine_resources.c.csv"
machine_resources_file_d = "./data/machine_resources.d.csv"
machine_resources_file_e = "./data/machine_resources.e.csv"

job_info_file_a = "outlineJobSort/time_A_job.csv"
job_info_file_b = "./data/job_info.b.csv"
job_info_file_c = "./data/job_info.c.csv"
job_info_file_d = "./data/job_info.d.csv"
job_info_file_e = "./data/job_info.e.csv"


# # refined solution
refinedSolution_file = "./submit/refinedsolution.csv"


olddata_app_interference_file = 'data/olddata/scheduling_preliminary_app_interference_20180606.csv'

outfile = open(refinedSolution_file, 'w')


class App:

    def __init__(self, app_id, cpu, mem, disk, P, M, PM):
        self.id = app_id
        self.cpu = cpu
        self.mem = mem
        self.disk = disk
        self.P = P
        self.M = M
        self.PM = PM
        self.instance = []
        self.stability = np.std(self.cpu)
        self.avgCpu = np.mean(self.cpu)
        self.intimateApps = set([])


class Job:

    def __init__(self, job_id, cpu, mem, number_of_instance, execution_time, dependency_task_id, range_1, range_2):
        self.id = job_id
        self.cpu = cpu
        self.mem = mem
        self.number_of_instance = number_of_instance
        self.execution_time = int((execution_time-0.5)//15 + 1)
        self.dependency_task_id = dependency_task_id
        self.left = range_1
        self.right = range_2
        self.starttime = -1
        self.endtime = -1

    def CreateTask(self, itemcpu, itemmem):
        # pass
        itemnumber1 = itemcpu // self.cpu + 1
        itemnumber2 = itemmem // self.mem + 1
        itemnumber = int(min(itemnumber1, itemnumber2))

        part = self.number_of_instance//itemnumber + 1
        number_jobs_in_task = [itemnumber] * (part-1)
        if self.number_of_instance - sum(number_jobs_in_task) > 0:
            number_jobs_in_task.append(
                self.number_of_instance - sum(number_jobs_in_task))
        else:
            part -= 1

        assert(sum(number_jobs_in_task) == self.number_of_instance)
        earlytime = self.left
        for depend in self.dependency_task_id:
            if len(depend) > 0:
                assert(Jobs[depend].endtime > 0)
                earlytime = max(earlytime, Jobs[depend].endtime)

        # print(earlytime, self.right)
        # if earlytime > self.right:
        #     earlytime = self.right
        # print(earlytime, self.right)
        assert(earlytime <= self.right)
        self.starttime = random.randint(earlytime, self.right)

        Tasklist = []
        i = 0
        for number in number_jobs_in_task:
            task_id = self.id + '_' + str(i)
            Tasklist.append(task_id)
            task = Task(task_id, self.cpu, self.mem,
                        number, self.execution_time, self.starttime)
            Tasks[task_id] = task
            i += 1

        self.endtime = self.starttime + self.execution_time

        return Tasklist


class Task:

    def __init__(self, id, cpuitem, memitem, number, timelong, starttime):
        self.id = id
        self.cpu = np.zeros((98))
        self.cpu[starttime:starttime +
                 timelong] = self.cpu[starttime:starttime+timelong] + cpuitem * number
        self.mem = np.zeros((98))
        self.mem[starttime:starttime +
                 timelong] = self.mem[starttime:starttime+timelong] + memitem * number
        self.machine = "0"
        self.number = number
        self.timelong = timelong
        self.starttime = starttime


class Machine:
    '''
    Machine class
    - Member variables
                1. List of Inst placed on the machine: insts(set)
                2. The number of each deployed app on the machine: appCounter(dictionary)
                3. Machine id: id(string)
                4. Total amount of resources of cpu: cpu(1*1 numpy array)
                5. Total memory resources: mem(1*1 numpy array)
                6. Disk total resources: disk (scalar)
                7. P: P (scalar)
                8. M: M (scalar)
                9. PM: PM (scalar)
                10. cpu usage rate: cpurate(float)
                11. cpu usage cap (optional): cputhreshold(float)
                12. Remaining cpu resources: rcpu(1*98 numpy array)
                13. Remaining mem resources: rmem(1*98 numpy array)
                14. Remaining disk resources: rdisk (scalar)
                15. Remaining P resources: rP()
                16. Remaining M resources:
    - member function
                1.init initialization
                2.available(self,inst_id): Check if inst_id(string) can be inserted into the current machine
                3.available(self,inst_id): Detect if inst_id(string) can be inserted into the current machine
                4.AvailableThresholdIns(self, inst_id): Check if the inst is added to the machine when the threshold is limited.
                5.add_inst(self, inst_id): add instance inst_id to the current machine
                6.remove(self, inst_id): Move out the instance inst_id
    '''

    def __init__(self, machine_id, cpu, mem, disk, P, M, PM):
        self.insts = set([])
        self.tasks = set([])
        self.appCounter = {}
        self.id = machine_id
        self.cpu = cpu
        self.mem = mem
        self.disk = disk
        self.P = P
        self.M = M
        self.PM = PM
        self.cputhreshold = 0.5
        self.cpurate = 0.0
        # Remaining resources
        self.rcpu = np.zeros((98)) + cpu
        self.rmem = np.zeros((98)) + mem
        self.rdisk = disk
        self.rP = P
        self.rM = M
        self.rPM = PM
        # estimate resources
        self.ecpu = np.zeros((98)) + cpu
        self.emem = np.zeros((98)) + mem
        self.edisk = disk
        self.eP = P
        self.eM = M
        self.ePM = PM
        # Current machine score
        self.score = 0.0
        self.alpha = 10
        self.beta = 0.5
        # Machine cpu stability
        self.stability = 0  # np.std(self.cpu-self.rcpu)
        # Mean value of cpu utilization
        self.avgCpurate = 0  # np.mean((self.cpu-self.rcpu)/self.cpu)
        self.hasempty = False
        self.uselesstrynumber = 0

    def Available100(self, inst_id):
        # Check if the inst_id can be added to the current machine
        # under the condition of 100% utilization

        curApp = Apps[Insts[inst_id][0]]
        # check  cpu
        compare = np.greater_equal(self.rcpu, curApp.cpu)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate cpu on "+ self.id)
            return False
        # check  mem
        compare = np.greater_equal(self.rmem, curApp.mem)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate mem on "+ self.id)
            return False
        # check  disk
        compare = self.rdisk >= curApp.disk
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate disk on "+ self.id)
            return False
        # check  P
        compare = self.rP >= curApp.P
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate P on "+ self.id)
            return False
        # check  M
        compare = self.rM >= curApp.M
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate M on "+ self.id)
            return False
        # check  PM
        compare = self.rPM >= curApp.PM
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate PM on "+ self.id)
            return False
        # check inferrence
        try:
            for appa in self.appCounter:
                if appa+" "+curApp.id in Inferrences:
                    if curApp.id not in self.appCounter:
                        if 1 > Inferrences[appa+" "+curApp.id]:
                            logger.debug(
                                inst_id+" Inferrence0 between "+appa+" "+curApp.id+" broken "+"on " + self.id)
                            # logger.debug(inst_id,str(self.insts),self.id)
                            # print(Inferrences[appa+" "+curApp.id])
                            return False
                    elif self.appCounter[curApp.id]+1 > (Inferrences[appa+" "+curApp.id]+(appa == curApp.id)):
                        logger.debug(inst_id+"Inferrence2 between " +
                                     appa+" "+curApp.id+" broken "+"on " + self.id)
                        # logger.debug(inst_id,str(self.insts),self.id)
                        return False

                if curApp.id+" "+appa in Inferrences:
                    # if curApp.id not in self.appCounter:
                    if (self.appCounter[appa] + (appa == curApp.id)) > (Inferrences[curApp.id+" "+appa] + (appa == curApp.id)):
                        logger.debug(inst_id+" Inferrence3 between " +
                                     curApp.id+" "+appa+" broken "+"on " + self.id)
                        return False
        except:
            logger.debug("Bad error allocate " +
                         inst_id + " of App "+curApp.id)
        # constraint satisfy
        return True

    def AvailableEmpty(self, inst_id):
        # Check if the inst_id can be added to the current machine
        # under the condition of 100% utilization

        curApp = Apps[Insts[inst_id][0]]
        # check  cpu
        compare = np.greater_equal(self.cpu, curApp.cpu)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate cpu on "+ self.id)
            return False
        # check  mem
        compare = np.greater_equal(self.mem, curApp.mem)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate mem on "+ self.id)
            return False
        # check  disk
        compare = self.disk >= curApp.disk
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate disk on "+ self.id)
            return False
        # check  P
        compare = self.P >= curApp.P
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate P on "+ self.id)
            return False
        # check  M
        compare = self.M >= curApp.M
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate M on "+ self.id)
            return False
        # check  PM
        compare = self.PM >= curApp.PM
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate PM on "+ self.id)
            return False
        # check inferrence
        try:
            for appa in self.appCounter:
                if appa+" "+curApp.id in Inferrences:
                    if curApp.id not in self.appCounter:
                        if 1 > Inferrences[appa+" "+curApp.id]:
                            logger.debug(
                                inst_id+" Inferrence0 between "+appa+" "+curApp.id+" broken "+"on " + self.id)
                            # logger.debug(inst_id,str(self.insts),self.id)
                            # print(Inferrences[appa+" "+curApp.id])
                            return False
                    elif self.appCounter[curApp.id]+1 > (Inferrences[appa+" "+curApp.id]+(appa == curApp.id)):
                        logger.debug(inst_id+"Inferrence2 between " +
                                     appa+" "+curApp.id+" broken "+"on " + self.id)
                        # logger.debug(inst_id,str(self.insts),self.id)
                        return False

                if curApp.id+" "+appa in Inferrences:
                    # if curApp.id not in self.appCounter:
                    if (self.appCounter[appa] + (appa == curApp.id)) > (Inferrences[curApp.id+" "+appa] + (appa == curApp.id)):
                        logger.debug(inst_id+" Inferrence3 between " +
                                     curApp.id+" "+appa+" broken "+"on " + self.id)
                        return False
        except:
            logger.debug("Bad error allocate " +
                         inst_id + " of App "+curApp.id)
        # constraint satisfy
        return True

    def AvailableThresholdTask(self, task_id):
        # Check if the inst_id can be added to the current machine
        # under the condition that the utilization is up to self.threshold

        curtask = Tasks[task_id]
        # check  cpu
        compare = np.greater_equal(self.rcpu, curtask.cpu)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            logger.debug(task_id+" fails to acllocate cpu on " + self.id)
            return False
        # check cpu threshold
        compare = self.cputhreshold >= np.max(
            (self.cpu - self.rcpu + curtask.cpu)/self.cpu)
        if(not compare):
            logger.debug(task_id+" break the cpu threshold " + self.id)
            return False
        # check  memory
        compare = np.greater_equal(self.rmem, curtask.mem)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate mem on "+ self.id)
            return False
        # constraint satisfy
        return True

    def Available100Task(self, task_id):
        # Check if the inst_id can be added to the current machine
        # under the condition that the utilization is up to self.threshold

        curtask = Tasks[task_id]
        # check  cpu
        compare = np.greater_equal(self.rcpu, curtask.cpu)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            logger.debug(task_id+" fails to acllocate cpu on " + self.id)
            return False

        # check  memory
        compare = np.greater_equal(self.rmem, curtask.mem)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate mem on "+ self.id)
            return False

        # constraint satisfy
        return True

    def AvailableThresholdIns(self, inst_id):
        # Check if the inst_id can be added to the current machine
        # under the condition that the utilization is up to self.threshold

        curApp = Apps[Insts[inst_id][0]]
        # check  cpu
        compare = np.greater_equal(self.rcpu, curApp.cpu)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            logger.debug(inst_id+" fails to acllocate cpu on " + self.id)
            return False
        # check cpu threshold
        compare = self.cputhreshold >= np.max(
            (self.cpu - self.rcpu + curApp.cpu)/self.cpu)
        if(not compare):
            logger.debug(inst_id+" break the cpu threshold " + self.id)
            return False
        # check  memory
        compare = np.greater_equal(self.rmem, curApp.mem)
        compare = reduce(lambda x, y: x & y, compare)
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate mem on "+ self.id)
            return False
        # check  disk
        compare = self.rdisk >= curApp.disk
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate disk on "+ self.id)
            return False
        # check  P
        compare = self.rP >= curApp.P
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate P on "+ self.id)
            return False
        # check  M
        compare = self.rM >= curApp.M
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate M on "+ self.id)
            return False
        # check  PM
        compare = self.rPM >= curApp.PM
        if(not compare):
            # logger.debug(inst_id+" fails to acllocate PM on "+ self.id)
            return False
        # check inferrence
        try:
            for appa in self.appCounter:
                if appa+" "+curApp.id in Inferrences:
                    if curApp.id not in self.appCounter:
                        if 1 > Inferrences[appa+" "+curApp.id]:
                            # logger.debug(inst_id+" Inferrence0 between "+appa+" "+curApp.id+" broken "+"on "+ self.id)
                            # logger.debug(inst_id,str(self.insts),self.id)
                            # print(Inferrences[appa+" "+curApp.id])
                            return False
                    elif self.appCounter[curApp.id]+1 > (Inferrences[appa+" "+curApp.id]+(appa == curApp.id)):
                        # logger.debug (inst_id+"Inferrence2 between "+appa+" "+curApp.id+" broken "+"on "+ self.id)
                        # logger.debug(inst_id,str(self.insts),self.id)
                        return False

                if curApp.id+" "+appa in Inferrences:
                    # if curApp.id not in self.appCounter:
                    if (self.appCounter[appa] + (appa == curApp.id)) > (Inferrences[curApp.id+" "+appa] + (appa == curApp.id)):
                        # logger.debug(inst_id+" Inferrence3 between "+curApp.id+" "+appa+" broken "+"on "+ self.id)
                        return False
        except:
            logger.debug("Bad error allocate " +
                         inst_id + " of App "+curApp.id)

        # constraint satisfy
        return True

    def AddInst(self, inst_id):
        # Add instance inst to machine's list

        self.insts.add(inst_id)
        # Add the current app to the machine count
        if Insts[inst_id][0] not in self.appCounter:
            self.appCounter[Insts[inst_id][0]] = 1
        else:
            self.appCounter[Insts[inst_id][0]] += 1
        # Correct the current deployment location of Inst
        Insts[inst_id][1] = self.id
        # Calculate the remaining cpu resources
        self.rcpu = self.rcpu - Apps[Insts[inst_id][0]].cpu
        self.ecpu = self.ecpu - Apps[Insts[inst_id][0]].cpu
        # Calculate cpu usage
        self.cpurate = max((self.cpu-self.rcpu)/self.cpu)
        # Calculate remaining mem resources
        self.rmem = self.rmem - Apps[Insts[inst_id][0]].mem
        self.emem = self.emem - Apps[Insts[inst_id][0]].mem
        # Calculate the remaining disk resources
        self.rdisk = self.rdisk - Apps[Insts[inst_id][0]].disk
        self.edisk = self.edisk - Apps[Insts[inst_id][0]].disk
        # Calculate the remaining P resources
        self.rP = self.rP - Apps[Insts[inst_id][0]].P
        self.eP = self.eP - Apps[Insts[inst_id][0]].P
        # Calculate the remaining P resources
        self.rM = self.rM - Apps[Insts[inst_id][0]].M
        self.eM = self.eM - Apps[Insts[inst_id][0]].M
        # Calculate the remaining PM resources
        self.rPM = self.rPM - Apps[Insts[inst_id][0]].PM
        self.ePM = self.ePM - Apps[Insts[inst_id][0]].PM
        # Update stability value
        self.UpdateStatus()
        return True

    def AddTask(self, task_id):
        # Add instance inst to machine's list

        self.tasks.add(task_id)
        # Correct the current deployment location of Inst
        Tasks[task_id].machine = self.id
        # Calculate the remaining cpu resources
        self.rcpu = self.rcpu - Tasks[task_id].cpu
        self.ecpu = self.ecpu - Tasks[task_id].cpu
        # Calculate cpu usage
        self.cpurate = max((self.cpu-self.rcpu)/self.cpu)
        # Calculate remaining mem resources
        self.rmem = self.rmem - Tasks[task_id].mem
        self.emem = self.emem - Tasks[task_id].mem
        # Update stability value
        self.UpdateStatus()
        return True

    def RemoveTask(self, task_id):
        # Add instance inst to machine's list

        self.tasks.remove(task_id)
        # Correct the current deployment location of Inst
        Tasks[task_id].machine = self.id
        # Calculate the remaining cpu resources
        self.rcpu = self.rcpu + Tasks[task_id].cpu
        # Calculate cpu usage
        self.cpurate = max((self.cpu-self.rcpu)/self.cpu)
        # Calculate remaining mem resources
        self.rmem = self.rmem + Tasks[task_id].mem
        # Update stability value
        self.UpdateStatus()
        return True

    def RemoveIns(self, inst_id):
        # Remove inst_id from machine
        self.insts.remove(inst_id)
        # Add the current app to the machine count
        self.appCounter[Insts[inst_id][0]] -= 1
        if self.appCounter[Insts[inst_id][0]] == 0:
            del self.appCounter[Insts[inst_id][0]]
        self.rcpu = self.rcpu + Apps[Insts[inst_id][0]].cpu
        self.cpurate = max((self.cpu-self.rcpu)/self.cpu)
        self.rmem = self.rmem + Apps[Insts[inst_id][0]].mem
        self.rdisk = self.rdisk + Apps[Insts[inst_id][0]].disk
        self.rP = self.rP + Apps[Insts[inst_id][0]].P
        self.rM = self.rM + Apps[Insts[inst_id][0]].M
        self.rPM = self.rPM + Apps[Insts[inst_id][0]].PM
        self.UpdateStatus()
        return True

    def ERemoveIns(self, inst_id):
        # Remove inst_id from machine
        assert(inst_id in self.insts)
        self.ecpu = self.ecpu + Apps[Insts[inst_id][0]].cpu
        # self.cpurate = max((self.cpu-self.rcpu)/self.cpu)
        self.emem = self.emem + Apps[Insts[inst_id][0]].mem
        self.edisk = self.edisk + Apps[Insts[inst_id][0]].disk
        self.eP = self.eP + Apps[Insts[inst_id][0]].P
        self.eM = self.eM + Apps[Insts[inst_id][0]].M
        self.ePM = self.ePM + Apps[Insts[inst_id][0]].PM
        return True

    def ScoreOfAddInst(self, inst_id):
        # Returns the increase in penalty score
        # after adding inst_id to the current machine

        curApp = Apps[Insts[inst_id][0]]
        newscore = 0
        oldscore = 0
        oldalpha = 1 + len(self.insts)
        for rate in (self.cpu-self.ecpu)/self.cpu:
            oldscore += (1 + oldalpha*(exp(rate)-1))
        oldscore /= 98
        newalpha = 2 + len(self.insts)
        for rate in (self.cpu-self.ecpu+curApp.cpu)/self.cpu:
            newscore += (1 + newalpha*(exp(rate)-1))
        newscore /= 98
        assert(oldscore <= newscore)

        return newscore-oldscore

    def ScoreOfAddTask(self, task_id):
        # Returns the increase in penalty score
        # after adding inst_id to the current machine
        # curtask = Tasks[task_id]

        curtask = Tasks[task_id]
        newscore = 0
        oldscore = 0
        oldalpha = 1 + len(self.insts)
        for rate in (self.cpu-self.ecpu)/self.cpu:
            oldscore += (1 + oldalpha*(exp(rate)-1))
        oldscore /= 98
        newalpha = 1 + len(self.insts)
        for rate in (self.cpu-self.ecpu+curtask.cpu)/self.cpu:
            newscore += (1 + newalpha*(exp(rate)-1))
        newscore /= 98
        assert(oldscore <= newscore)
        return newscore-oldscore

    def ScoreChangeOfRemoveInst(self, inst_id):
        # Returns the reduction in penalty score
        # after shifting out inst_id to the current machine

        curApp = Apps[Insts[inst_id][0]]
        score = 0
        if(len(self.insts) == 1):
            score = 0
        else:
            for rate in (self.cpu - (self.rcpu + curApp.cpu))/self.cpu:
                score += (1 + self.alpha*(exp(max(rate-self.beta, 0))-1))
        return score - self.score

    def IncreaseThreshold(self, threhold):
        # Change the upper limit of the current machine's CPU usage
        self.cputhreshold = threhold

    # The following is an internal status update function
    # that does not need to be called externally.
    def ResetStatus(self):
        # reset the current machine status with 0

        if len(self.insts) == 0:
            self.cpurate = 0.0
            # Remaining resources
            self.rcpu = self.cpu
            self.rmem = self.mem
            self.rdisk = self.disk
            self.rP = self.P
            self.rM = self.M
            self.rPM = self.PM
            # Current machine score
            self.score = 0.0
            # Machine cpu stability
            self.stability = 0  # np.std(self.cpu-self.rcpu)
            # Mean value of cpu utilization
            self.avgCpurate = 0  # np.mean((self.cpu-self.rcpu)/self.cpu)

    def UpdateStatus(self):
        # Update the current machine status,
        # including scores, stability, average utilization, etc.

        if(len(self.insts) == 0 and len(self.tasks) == 0):
            self.ResetStatus()
        else:
            # 更新当前机器的得分
            self.UpdateScore()
            # 更新稳定性和平均利用率
            self.stability = np.std(self.cpu-self.rcpu)
            self.avgCpurate = np.mean((self.cpu-self.rcpu)/self.cpu)

    def UpdateScore(self):
        # Update the score of the current machine

        self.score = 0
        if len(self.insts) == 0 and len(self.tasks) == 0:
            self.score = 0
        else:
            self.alpha = 1 + len(self.insts)
            for rate in (self.cpu-self.rcpu)/self.cpu:
                self.score += (1 + self.alpha*(exp(max(rate-self.beta, 0))-1))
        self.score /= 98
        # print("number of grater than 0.5 {}".format(count))
        return True


def CaculateScore():
    # calculate the score we get for each machine

    score = 0
    emptynum = 0
    for machine in Machines:
        Machines[machine].UpdateScore()
        score += Machines[machine].score
        if len(Machines[machine].insts) == 0 and len(Machines[machine].tasks) == 0:
            emptynum += 1
    print("empty machine is {}".format(emptynum))
    return score


def FindSatisfyIns(inst_id):
    # find the most satisfy machine for ins, in the stage of first fit

    machinelist = list(Machines)
    randlist = random.sample(machinelist, len(machinelist))

    for machine in randlist:
        if Machines[machine].hasempty == False and Machines[machine].AvailableEmpty(inst_id):
            return machine
    return 'no find'


def ReallocateTask(task_id, machine_id=""):
    # find another satisfy machine for task.
    # if cant find the good one, return ":"

    machinelist = list(set(Machines).difference(set(CutMachines)))
    # machinelist = list(Machines)
    randlist = random.sample(machinelist, len(machinelist))
    for machine_id in randlist:
        if Machines[machine_id].AvailableThresholdTask(task_id):
            Machines[machine_id].AddTask(task_id)
            return machine_id

    return ":"


def CheckThresholdReturnScore(inst_id, machine_id):
    # used in greedy algorithm, the increasing of the score can determine the
    # value of putting.

    score_change = 100

    if Machines[machine_id].uselesstrynumber < 10000 and Machines[machine_id].Available100(inst_id):
        score_change = Machines[machine_id].ScoreOfAddInst(inst_id)
    else:
        Machines[machine_id].uselesstrynumber += 1
    return score_change


def TaskCheckThresholdReturnScore(task_id, machine_id):
    # used in greedy algorithm, the increasing of the score can determine the
    # value of putting.

    score_change = 100

    if Machines[machine_id].uselesstrynumber < 10000 and Machines[machine_id].Available100Task(task_id):
        score_change = Machines[machine_id].ScoreOfAddTask(task_id)

    return score_change


def PartReallocateInsAsScore(inst_id, machine_id=""):
    # used in greedy algorithm, the increasing of the score can determine the
    # value of putting.
    # but this part will not check every machine.

    part_large = 300

    machinelist = list(set(Machines).difference(set(CutMachines)))
    # machinelist = list(Machines)-CutMachines
    randlist = random.sample(machinelist, len(machinelist))
    best_machine = 'unknown'
    best_score = 100
    # test = []

    loop = 0
    for machine_id in randlist:

        current_score = CheckThresholdReturnScore(inst_id, machine_id)

        if current_score != 100 and best_score > current_score:
            best_score = current_score
            best_machine = machine_id

        if loop > part_large and best_score != 'unknown':
            break
        loop += 1

    if best_machine in machinelist:
        Machines[best_machine].AddInst(inst_id)
    return best_machine


def PartReallocateTaskAsScore(task_id, machine_id=""):
    # used in greedy algorithm, the increasing of the score can determine the
    # value of putting.
    # but this part will not check every machine.

    part_large = 300

    machinelist = list(set(Machines).difference(set(CutMachines)))
    # machinelist = list(Machines)-CutMachines
    randlist = random.sample(machinelist, len(machinelist))
    best_machine = 'unknown'
    best_score = 100

    loop = 0
    for machine_id in randlist:
        current_score = TaskCheckThresholdReturnScore(task_id, machine_id)
        if current_score != 100 and best_score > current_score:
            best_score = current_score
            best_machine = machine_id
        if loop > part_large and best_score != 'unknown':
            break
        loop += 1
    if best_machine in machinelist:
        Machines[best_machine].AddTask(task_id)
    return best_machine


def ReallocateInsAsScore(inst_id, machine_id=""):
    # used in greedy algorithm, the increasing of the score can determine the
    # value of putting.
    # but this part will not check every machine.

    machinelist = list(Machines)
    randlist = random.sample(machinelist, len(machinelist))
    best_machine = 'unknown'
    best_score = 100

    for machine_id in randlist:
        current_score = CheckThresholdReturnScore(inst_id, machine_id)
        if current_score != 100 and best_score > current_score:
            best_score = current_score
            best_machine = machine_id

    if best_machine in machinelist:
        Machines[best_machine].AddInst(inst_id)
    # print("successful schedual {} to {}".format(inst_id, best_machine))
    return best_machine


def ReallocateIns(inst_id, machine_id=""):
    # relocate teh ins

    machinelist = list(Machines)
    randlist = random.sample(machinelist, len(machinelist))

    for machine_id in randlist:
        if Machines[machine_id].AvailableThresholdIns(inst_id):
            Machines[machine_id].AddInst(inst_id)
            return machine_id
    return ":"


def Reallocate100persentIns(inst_id, machine_id=""):
    machinelist = list(Machines)
    randlist = random.sample(machinelist, len(machinelist))

    for machine_id in randlist:
        if Machines[machine_id].Available100(inst_id):
            Machines[machine_id].AddInst(inst_id)
            print("relocate 100 success ins {} to machine {}".format(
                inst_id, machine_id))
            return machine_id
    print("relocate 100 failed {}".format(inst_id))
    return ":"


def Reallocate100persentTasks(task_id, machine_id=""):

    machinelist = list(set(Machines).difference(set(CutMachines)))
    randlist = random.sample(machinelist, len(machinelist))

    for machine_id in randlist:
        if Machines[machine_id].Available100Task(task_id):
            Machines[machine_id].AddTask(task_id)
            print("relocate 100 success Task {} to machine {}".format(
                task_id, machine_id))
            return machine_id
    print("100 persent relocate failed {}".format(task_id))
    return ":"


def PutInsToMachineAndCheckIns(inst_id, machine_id=""):

    if(Machines[machine_id].AvailableThresholdIns(inst_id)):
        Machines[machine_id].AddInst(inst_id)
        return machine_id
    else:
        return "Threshold"


def PutInsToMachineWithoutCheck(inst_id, machine_id=""):

    Machines[machine_id].AddInst(inst_id)
    return machine_id
