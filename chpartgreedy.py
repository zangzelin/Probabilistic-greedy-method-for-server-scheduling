from util import *
from newloaddata import *
import sys

# Compaired to greedy.py
# this algorithm improve the method of muti-loop.


def sortOutput(ins_changelist, task_changelist, text, allscore,cn):
    # print(rawOutput)
    outfile = open("./zzl/submit/"+text+str(allscore)+"_"+str(cn)+".csv", 'w')

    for task, machine in ins_changelist[0]:
        assert(machine in Machines)
        outfile.write("1,"+task+","+machine+'\n')

    for task, machine in ins_changelist[1]:
        assert(machine in Machines)
        outfile.write("2,"+task+","+machine+'\n')

    for task, machine in ins_changelist[2]:
        assert(machine in Machines)
        outfile.write("3,"+task+","+machine+'\n')

    for task, machine in task_changelist:
        assert(machine in Machines)
        job_id = task.split('_')[0]
        machine_id = machine
        start_time = str(15 * Tasks[task].starttime)
        number = str(Tasks[task].number)

        outfile.write(job_id+","+machine_id+","+start_time+","+number+'\n')

    return 0


def LoadInsStep1():
    changelist = []
    brokenlist = []
    for inst, app, machine in PreDeploy:
        # assert(len(machine) > 1)
        # number_of_machine = int(machine.split('_')[1])
        if (machine in CutMachines) or (not Machines[machine].AvailableThresholdIns(inst)):
            brokenlist.append([inst, app, machine])
        PutInsToMachineWithoutCheck(inst, machine)

    print("Ins Step 1: {} ins has been put into machine without check! \n and fins {} item broken the constraint ".format(
        len(PreDeploy), len(brokenlist)))

    return changelist, brokenlist


def LoadInsStep2(brokenlist, sort_ins_list):

    changelist = []
    removelist = []
    inscantdeal = []
    process = 0
    allnumber = len(brokenlist)

    brokenlistins = []
    for ins_s, app_s, mach_s in brokenlist:
        brokenlistins.append(ins_s)
        Machines[mach_s].ERemoveIns(ins_s)

    for i in range(len(Insts)):
        inst = 'inst_'+str(int(sort_ins_list[i, 0]))
        app = Insts[inst][0]
        machine = Insts[inst][1]

        if inst in brokenlistins:
            if process % 1000 == 0:
                print('Ins Step 2: finish {}%'.format(process/allnumber))
            process += 1

            new_machine = PartReallocateInsAsScore(inst)
            if new_machine not in list(Machines):
                inscantdeal.append([inst, '0', machine])
            else:

                removelist.append([inst, machine])
                changelist += [[inst, new_machine]]

    print("after step 2.1: {} broken ins has been put into another machine! \n and still {} inst to deal next loop".format(
        len(brokenlist)-len(inscantdeal), len(inscantdeal)))

    for inst, machine in removelist:
        Machines[machine].RemoveIns(inst)

    for machine in Machines:
        Machines[machine].uselesstrynumber = 0

    return changelist, inscantdeal


def ReLoadInsStep2(sort_ins_list):

    changelist = []
    removelist = []
    inscantdeal = []
    process = 0

    brokenlist = []

    for machine in Machines:
        Machines[machine].UpdateScore()
        Machines[machine].UpdateStatus()
        # input(str(Machines[machine].score))
        if Machines[machine].stability > 5 or Machines[machine].score >1.5 :
            ave = 0
            inslist = list(Machines[machine].insts)
            for ins in inslist:
                ave += Apps[Insts[ins][0]].stability
            ave /= len(inslist)
            for ins in inslist:
                if Apps[Insts[ins][0]].stability>ave:
                    brokenlist.append([ins, '0', machine])

    print("in ReloadInstep 2 , find {} ins to be reload".format(len(brokenlist)))

    allnumber = len(brokenlist)

    brokenlistins = []
    for ins_s, app_s, mach_s in brokenlist:
        brokenlistins.append(ins_s)
        Machines[mach_s].ERemoveIns(ins_s)



    for i in range(len(Insts)):
        inst = 'inst_'+str(int(sort_ins_list[i, 0]))
        app = Insts[inst][0]
        machine = Insts[inst][1]

        if inst in brokenlistins:
            if process % 1000 == 0:
                print('step 2: finish {}%'.format(process/allnumber))
            process += 1

            new_machine = PartReallocateInsAsScore(inst)
            if new_machine not in list(Machines):
                inscantdeal.append([inst, '0', '0'])
            else:
                removelist.append([inst, machine])
                changelist += [[inst, new_machine]]

    print("after step 2.1: {} broken ins has been put into another machine! \n and still {} inst to deal next loop".format(
        len(brokenlist)-len(inscantdeal), len(inscantdeal)))

    for inst, machine in removelist:
        Machines[machine].RemoveIns(inst)

    for machine in Machines:
        Machines[machine].uselesstrynumber = 0

    return changelist, inscantdeal


def LoadTaskStep1():
    # pass
    process = 0
    allnumber = len(Joblist)
    changelist = []
    num_hundred = 0

    for job in Joblist:
        if process % 100 == 0:
            print('Task step 1 : finish {}%'.format(process/allnumber))
        process += 1

        Tasklist = Jobs[job].CreateTask(5, 5)
        for task_id in Tasklist:
            new_machine = ReallocateTask(task_id)
            # new_machine = PartReallocateTaskAsScore(task_id)

            if new_machine not in Machines:
                new_machine_100 = Reallocate100persentTasks(task_id)

                if new_machine_100 not in list(Machines):
                    print('have to use strong method or split the task!!')
                    input("stop to deal with !!")
                else:
                    changelist_current = [[task_id, new_machine_100]]
                    num_hundred += 1

            else:
                changelist_current = [[task_id, new_machine]]

            changelist += changelist_current

    return changelist


def CutMachine(num):

    for i in range(num):
        # Machines.pop()
        CutMachines.append("machine_"+str(i+1))
        # assert(len(Machines) == 8000 - i - 1)


def solute(text, cutnumber):
    # text = 'a'
    sort_ins_list = Loaddata(text)
    Globalthreshold = 0.4
    for machine in Machines:
        Machines[machine].IncreaseThreshold(Globalthreshold)

    CutMachine(cutnumber)
    changelist1, brokenlist = LoadInsStep1()
    # input(len(changelist1))
    changelist2, inscantdeal1 = LoadInsStep2(brokenlist, sort_ins_list)
    allscore = CaculateScore()
    print('finsh probel {}, score is {}'.format(text, allscore))
        
    changelist3, inscantdeal2 = LoadInsStep2(inscantdeal1, sort_ins_list)
    allscore = CaculateScore()
    print('finsh probel {}, score is {}'.format(text, allscore))
    changelist4, inscantdeal3 = LoadInsStep2(inscantdeal2, sort_ins_list)
    allscore = CaculateScore()
    print('finsh probel {}, score is {}'.format(text, allscore))

    task_changelist = LoadTaskStep1()

    changelist = [changelist1, changelist2, changelist3]
    # changelist = [[], []]
    allscore = CaculateScore()
    sortOutput(changelist, task_changelist, text, allscore,cutnumber)

    print('finsh probel {}, score is {}'.format(text, allscore))


def Creatfinalfile():
    file_a_path = 'zzl/submit/a6262.csv'
    file_b_path = 'zzl/submit/b6469.csv'
    file_c_path = 'zzl/submit/c9119.csv'
    file_d_path = 'zzl/submit/d7777.csv'
    file_e_path = 'zzl/submit/e10317.csv'

    outfile = open("./zzl/submit/final_1.csv", 'w')

    file_a = open(file_a_path)
    for line in file_a:
        outfile.write(line)
    outfile.write('#\n')

    file_b = open(file_b_path)
    for line in file_b:
        outfile.write(line)
    outfile.write('#\n')

    file_c = open(file_c_path)
    for line in file_c:
        outfile.write(line)
    outfile.write('#\n')

    file_d = open(file_d_path)
    for line in file_d:
        outfile.write(line)
    outfile.write('#\n')

    file_e = open(file_e_path)
    for line in file_e:
        outfile.write(line)
    # outfile.write('#\n')


def check():
    for machine in Machines:
        assert(np.min(Machines[machine].rcpu) >= 0)
        assert(np.min(Machines[machine].rmem) >= 0)
        assert(np.min(Machines[machine].rdisk) >= 0)


if __name__ == '__main__':

    import sys
    print("dealing with problem {} use machine {}".format(
        sys.argv[1], sys.argv[2]))
    if sys.argv[1] != 'add':
        solute(sys.argv[1], int(sys.argv[2]))
    else:
        Creatfinalfile()
