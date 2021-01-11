from requests import get
import atexit
from apscheduler.schedulers.blocking import BlockingScheduler
import git

def auto_push_git():
    PATH_OF_GIT_REPO = '.' 
    COMMIT_MESSAGE = 'auto update public ip'
    print('auto push to git')
    try:
        repo = git.Repo(PATH_OF_GIT_REPO)
        repo.git.add(update=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin = repo.remote('Emergency-Deployed')
        origin.push()
        print('push to branch Emergency-Deployed complete')

        repo = git.Repo(PATH_OF_GIT_REPO)
        current = repo.branches['Emergency-Deployed']
        main = repo.branches['Deploy']
        base = repo.merge_base(current, main)
        repo.index.merge_tree(main, base=base)
        repo.index.commit('Merge main into feature',parent_commits=(current.commit, main.commit))
        current.checkout(force=True)

        print('merge branch Emergency-Deployed to branch Deploy complete')
    except:
        print('Some error occured while pushing the code') 

    return None   


def change_ip():
    env_dir = ".env.emergency"
    setting_dir = "./BackTaxDeductSystem/settings.py"

    new_ip = get('https://api.ipify.org').text
    print('My public IP address is: {}'.format(new_ip))

    old_ip = None
    f = open(env_dir, "r")
    for x in f:
        if 'HOST_DB=' in x:
            old_ip = x[x.index('=')+1:-1]
            print('My Old public IP address is: {}'.format(old_ip))
            break
    f.close()

    if not old_ip or new_ip != old_ip:
        print('public IP address is changed to: {}'.format(new_ip))
        
        #change in env
        f = open(env_dir, "r")
        temp_lines = []
        for x in f:
            temp_lines.append(x)
        f.close()

        for x in temp_lines:
            if old_ip in x:
                index = temp_lines.index(x)
                temp_lines[index] = x.replace(old_ip,new_ip)
                break

        temp_all = ''
        for x in temp_lines:
            temp_all += x
        f = open(env_dir, "w")
        f.write(temp_all)
        f.close()

        #change in setting
        f = open(setting_dir, "r")
        temp_lines = []
        for x in f:
            temp_lines.append(x)
        f.close()

        for x in temp_lines:
            if old_ip in x:
                index = temp_lines.index(x)
                temp_lines[index] = x.replace(old_ip,new_ip)
        
        temp_all = ''
        for x in temp_lines:
            temp_all += x
        f = open(setting_dir, "w")
        f.write(temp_all)
        f.close()

        auto_push_git()

    elif new_ip == old_ip :
        print('public IP address not change')
    
    print()



#scheduler = BlockingScheduler() 
#scheduler.add_job(func=change_ip, trigger="interval", seconds=5)
#scheduler.start()

# Shut down the scheduler when exiting the app
#atexit.register(lambda: scheduler.shutdown())

auto_push_git()


