import argparse
import os
import subprocess
from datetime import datetime
import pymysql
from tqdm import tqdm


#Repositories = {
#    'mall-root': 'C:\\Users\\geesi\\Desktop\\BQ\\mall-root',
#    'bnq_root': 'C:\\Users\\geesi\\Desktop\\BQ\\bnq_root',
#    'bnq_owner_ios': 'C:\\Users\\geesi\\Desktop\\BQ\\bnq_owner_ios',
#}

"""parsing and configuration"""
def parse_args():
    desc = "Retrieve commits from git"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--git_base_path', type=str, default='C:\\Users\\geesi\\Desktop\\BQ',
                        help='Git base path')

    return parser.parse_args()

def git_sync(git_path):
    os.chdir(git_path)
    subprocess.run(['git', 'pull'])

def get_git_commits(git_path, last_date):
    cmd = ['git','log', 'master', '--pretty=format:"%H,%cn,%ce,%ct"', 
            '--numstat', '--no-merges']
    if last_date:
        cmd.append('--since="%s"'%last_date.strftime('%Y-%m-%d %H:%M:%S'))

    os.chdir(git_path)
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    raw_output = result.stdout
    raw_output = raw_output.decode('utf-8')
    return raw_output.split('\n')

def insert_commit(dbcon, commit, changes):
    with dbcon.cursor() as cursor:
        #Use Ignore to ignore same commit to be counted multiple times
        commit_sql = "INSERT IGNORE INTO commit (`hash`, `user`, `email`, `commit_date`, \
                    `insert`, `delete`, `files`, `project_name`, `repository_id`) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        changes_sql = "INSERT INTO file_changes (`commit_id`, `insert`, `delete`, `file_name`) \
                        VALUES (%s, %s, %s, %s)"
        
        if(cursor.execute(commit_sql, commit) > 0):
            change_values = [[cursor.lastrowid] + c for c in changes]
            cursor.executemany(changes_sql, change_values)
        
        dbcon.commit()

def write_log(dbcon, project_id, commit_processed, last_hash, last_date):
    with dbcon.cursor() as cursor:
        log_sql = "INSERT INTO log (`project_id`, `commit_processed`, `last_hash`, `last_date`) VALUES (%s, %s, %s, %s)"
        cursor.execute(log_sql, (project_id, commit_processed,last_hash, last_date))

def parse_commit_line(commit_line, summary, project_name, repository_id):
    summary[0:4] = commit_line.strip('"').split(',')
    summary[0] = summary[0][:40]
    summary[1] = summary[1][:20]
    summary[2] = summary[1][:40]
    summary[3] = datetime.fromtimestamp(int(summary[3]))
    summary[4:7] = [0, 0, 0]
    summary[7] = project_name
    summary[8] = repository_id


def write_commit(dbcon, commit_lines, project_name, repository_id):
    commit_summary = [i for i in range(9)]
    changes = []
    commit_num = 0
    in_analyzing_changes = False

    for line in tqdm(commit_lines):
        if len(line) == 0:
            if in_analyzing_changes:
                insert_commit(dbcon, commit_summary, changes)
                commit_num += 1
                in_analyzing_changes = False
        else:
            if not in_analyzing_changes:
                parse_commit_line(line, commit_summary, project_name, repository_id)
                in_analyzing_changes = True
                changes = []
            else:
                c = line.split('\t')
                if len(c) == 3:
                    c[0] = int(c[0]) if c[0] != '-' else 0
                    c[1] = int(c[1]) if c[1] != '-' else 0
                    commit_summary[4] += c[0]
                    commit_summary[5] += c[0]
                    commit_summary[6] += 1
                    changes.append(c)
                else:  #In case the previous commit log has no change
                    insert_commit(dbcon, commit_summary, changes)
                    commit_num += 1
                    parse_commit_line(line, commit_summary, project_name, repository_id)
            
    if in_analyzing_changes:
        insert_commit(dbcon, commit_summary, changes)
        commit_num += 1
    
    return (commit_num, commit_summary[0], commit_summary[3])

def get_repositories(dbcon):
    with dbcon.cursor() as cursor:
        query_sql = "SELECT `id`, `project_name`, `repository_name` from repository order by `project_name`"
        cursor.execute(query_sql)
        rows = cursor.fetchall()
    
    return rows

def get_last_date(dbcon, project_id):
    last_date = 0
    with dbcon.cursor() as cursor:
        log_query = "SELECT last_date from log where project_id = %s order by last_date limit 1"
        if cursor.execute(log_query % project_id) > 0:
            last_date = cursor.fetchone()[0]

    return last_date

def main(args):
    dbcon = pymysql.connect(host="localhost", user="giter", passwd="giter=01", db="gitwork", charset="utf8")
    
    repositories = get_repositories(dbcon)

    for project_id, project_name, repository_name in repositories:
        print('Processing %s/%s'%(project_name, repository_name))
        git_path = os.path.join(args.git_base_path, project_name, repository_name)
        
        print('Syncronizing %s...'%(git_path))
        git_sync(git_path)
        
        print('Analyzing git log')
        last_date = get_last_date(dbcon, project_id)

        commits = get_git_commits(git_path, last_date)
        n, last_hash, last_date = write_commit(dbcon, commits, project_name, project_id)

        write_log(dbcon, project_id, n, last_hash, last_date)
        print('Total %d commits processed'%n)
    
    dbcon.close()

if __name__ == '__main__':
    # parse arguments
    args = parse_args()
    if args is None:
        exit()

    # main
    main(args)