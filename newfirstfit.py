import sys

from newloaddata import *
from util import *


'''
This method is a basic firstfit method, and this method can be divided into four part:
    LoadInsStep1, load the instrance which running in the machines and add the bad instrance into a list( brokenlist )
    LoadInsStep2, relocate the instrance in brokenlist, and find the instrance can not dealwith in this loop
    LoadInsStep3, relocate the instrance in brokenlist, and find the instrance can not dealwith in this loop
    LoadTaskStep1, create the task in job.csv, and random relocate it. 
'''

def sortOutput(ins_changelist, task_changelist, text, allscore):
    # This function create the output file with two change list
    # Input :
    #       ins_changelist, the change list of instrance
    #       task_changelist, the change list of task
    #       text, the problem name current dealing with
    #       allscore, the score of this scheduling calculated in this problem
    # Output :
    #       a file named 'outfile' in /submit/

    outfile = open("./submit/"+text+str(allscore)+".csv", 'w')

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


def StrongRelocateIns(inst, removelist):
    # This function used to relocate the instrance that can not locate by function RelocateIns
    # This function do not consider the constrains of 0.5 cpu
    # Input:
    #       inst, the name of current instrance
    # Output:
    #       changelist2, the list of ins->machine change in this relocate
    #       changelinstnextloop, the list of ins that  need to be deal with in next scheduling loop
    #       removelist, the list of ins to be remove at the end of this list.

    changelist2 = []
    changelinstnextloop = []
    print("Stronge Relocate ins {} ".format(inst))

    machinelist = list(Machines)
    machine_id = FindSatisfyIns(inst)
    if machine_id in machinelist:

        instlist = Machines[machine_id].insts
        for inst_id in list(instlist):
            # Machines[machine_id].RemoveIns(inst_id)
            removelist.append([inst_id, machine_id])
            new_machine = ReallocateIns(inst_id)
            # if new_machine in machinelist:
            if new_machine not in list(Machines):
                changelistcurrent, changelinstnextloopcurrent, removelist = StrongRelocateIns(
                    inst_id, removelist)
                changelist2 += changelistcurrent
                changelinstnextloop += changelinstnextloopcurrent
            else:
                changelist2.append([inst_id, new_machine])

        Machines[machine_id].hasempty = True
        changelinstnextloop.append([inst, machine_id])

    return changelist2, changelinstnextloop, removelist


def LoadInsStep1():
    # This function load the instrance which running in the machines
    # And the bad instrance ( over 0.5 cpu ) is record in a list.
    # Input:
    #       no in put
    # Output:
    #       brokenlist, the list of bad instrance, and this ins will be relocate next step.

    brokenlist = []
    for inst, app, machine in PreDeploy:
        assert(len(machine) > 1)
        if Machines[machine].AvailableThresholdIns(inst):
            pass
        else:
            brokenlist.append([inst, app, machine])
        PutInsToMachineWithoutCheck(inst, machine)

    print("after step 1: {} ins has been put into machine without check! \n and fins {} item broken the constraint ".format(
        len(PreDeploy), len(brokenlist)))

    return brokenlist


def LoadInsStep2(brokenlist, sort_ins_list):
    # This function reload the bad instrance in step 1
    # And find the instrance cant be load in this loop
    # Input:
    #       brokenlist, the list of bad instrance in step 1
    #       sort_ins_list, the list of instrance queued by importance.
    # Output:
    #       changelist,
    #       changelinstnextloop, the list of bad instrance, and this ins will be relocate next step.

    changelist = []
    removelist = []
    changelinstnextloop = []
    num_hundred = 0
    num_strong = 0
    process = 0
    allnumber = len(brokenlist)

    brokenlistins = []
    for ins_s, app_s, mach_s in brokenlist:
        brokenlistins.append(ins_s)

    for i in range(len(Insts)):
        inst = 'inst_'+str(int(sort_ins_list[i, 0]))
        app = Insts[inst][0]
        machine = Insts[inst][1]

        if inst in brokenlistins:
            if process % 1000 == 0:
                print('step 2: finish {}%'.format(process/allnumber))
            process += 1

            # Machines[machine].RemoveIns(inst)
            removelist.append([inst, machine])

            new_machine = ReallocateIns(inst)

            # if can not find a good machine for instrance, then use the strong reloat func to find one
            if new_machine not in list(Machines):
                new_machine_100 = Reallocate100persentIns(inst)
                if new_machine_100 not in list(Machines):
                    changelist_current, changelinstnextloop, removelist = StrongRelocateIns(
                        inst, removelist)
                    num_strong += 1
                else:
                    changelist_current = [[inst, new_machine_100]]
                    num_hundred += 1
            else:
                changelist_current = [[inst, new_machine]]
            changelist += changelist_current

    print("after step 2: {} broken ins has been put into another machine! \n and  {} strong relocate".format(
        len(brokenlist), num_strong))

    for inst, machine in removelist:
        Machines[machine].RemoveIns(inst)

    for inst, machine in changelinstnextloop:
        information = PutInsToMachineAndCheckIns(inst, machine)
        assert(information in list(Machines))

    return changelist, changelinstnextloop


def LoadInsStep3(sort_ins_list):
    # This function reload the bad instrance in step 2
    # And find the instrance cant be load in this loop
    # Input:
    #       sort_ins_list, the list of instrance queued by importance.
    # Output:
    #       changelist,
    #       changelinstnextloop, the list of bad instrance, and this ins will be relocate next step.
    changelist = []
    changelinstnextloop = []
    removelist = []
    num_hundred = 0
    num_strong = 0

    process = 0
    allnumber = len(NonDeploy)
    # NonDeploy.reverse()
    for i in range(len(Insts)):

        inst = 'inst_'+str(int(sort_ins_list[i, 0]))
        app = Insts[inst][0]
        machine = Insts[inst][1]

        if machine == None:
            if process % 1000 == 0:
                print('step 3: finish {}%'.format(process/allnumber))
            process += 1

            new_machine = ReallocateIns(inst)
            if new_machine not in list(Machines):
                new_machine_100 = Reallocate100persentIns(inst)
                if new_machine_100 not in list(Machines):
                    changelist_current, changelinstnextloop, removelist = StrongRelocateIns(
                        inst, removelist)
                    num_strong += 1
                else:
                    changelist_current = [[inst, new_machine_100]]
                    num_hundred += 1
            else:
                changelist_current = [[inst, new_machine]]

            changelist += changelist_current

    print("after step 3: {} NonDeploy ins has been put into another machine! \n and  {} strong relocate, {} hundrade relocate".format(
        len(NonDeploy), num_strong, num_hundred))

    for inst, machine in removelist:
        Machines[machine].RemoveIns(inst)

    for inst, machine in changelinstnextloop:
        information = PutInsToMachineAndCheckIns(inst, machine)
        assert(information in list(Machines))

    return changelist, changelinstnextloop


def LoadTaskStep1():
    # This function create and schedule the task
    # Input:
    #       no
    # Output:
    #       changelist, the list to output

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


def solute(text, Globalthreshold):

    sort_ins_list = Loaddata(text)
    Globalthreshold = 1
    for machine in Machines:
        Machines[machine].IncreaseThreshold(Globalthreshold)

    brokenlist = LoadInsStep1()
    changelist2, changelist2next = LoadInsStep2(brokenlist, sort_ins_list)
    changelist3, changelist3next = LoadInsStep3(sort_ins_list)

    task_changelist = LoadTaskStep1()

    changelist = [changelist2, changelist3+changelist2next, changelist3next]
    allscore = CaculateScore()
    sortOutput(changelist, task_changelist, text, allscore)

    print('finsh probel {}, score is {}'.format(text, allscore))


def Createfinalfile():
    file_a_path = 'submit/a0.csv'
    file_b_path = 'submit/b0.csv'
    file_c_path = 'submit/c0.csv'
    file_d_path = 'submit/d0.csv'
    file_e_path = 'submit/e0.csv'

    outfile = open("./submit/final_1.csv", 'w')

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


if __name__ == '__main__':

    import sys
    if sys.argv[1] != 'add':
        print("dealing with problem {} thr {}".format(
            sys.argv[1], sys.argv[2]))
        solute(sys.argv[1], float(sys.argv[2]))
    else:
        Createfinalfile()
