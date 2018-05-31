import argparse
import os
import subprocess
from datetime import datetime
import pymysql
from tqdm import tqdm


Repositories = {
    'mall-root': 'C:\\Users\\geesi\\Desktop\\BQ\\mall-root',
    'bnq_root': 'C:\\Users\\geesi\\Desktop\\BQ\\bnq_root',
    'bnq_owner_ios': 'C:\\Users\\geesi\\Desktop\\BQ\\bnq_owner_ios',
}

"""parsing and configuration"""
def parse_args():
    desc = "Retrieve commits from git"
    parser = argparse.ArgumentParser(description=desc)

    return parser.parse_args()

def get_git_commits(git_path):
    os.chdir(git_path)
    result = subprocess.run(['git','log', 'master', 
                                '--pretty=format:"%H,%cn,%ce,%ct"', 
                                '--numstat', '--no-merges'], stdout=subprocess.PIPE)
    raw_output = result.stdout
    raw_output = raw_output.decode('utf-8')
    return raw_output.split('\n')

def insert_commit(dbcon, commit, changes):
    with dbcon.cursor() as cursor:
        commit_sql = "INSERT INTO commit (`hash`, `user`, `email`, `commit_date`, `insert`, `delete`, `files`, `repository`)\
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        changes_sql = "INSERT INTO file_changes (`commit_id`, `insert`, `delete`, `file_name`)\
        VALUES (%s, %s, %s, %s)"
        
        cursor.execute(commit_sql, commit)
        
        change_values = [[cursor.lastrowid] + c for c in changes]
        cursor.executemany(changes_sql, change_values)
        
        dbcon.commit()

def parse_commit_line(commit_line, summary):
    summary[0:4] = commit_line.strip('"').split(',')
    summary[3] = datetime.fromtimestamp(int(summary[3]))
    summary[4:7] = [0, 0, 0]

def write_commit(dbcon, commit_lines, repository_name):
    commit_summary = [i for i in range(8)]
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
                parse_commit_line(line, commit_summary)
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
                    commit_summary[7] = repository_name
                    changes.append(c)
                else:  #In case the previous commit log has no change
                    insert_commit(dbcon, commit_summary, changes)
                    commit_num += 1
                    parse_commit_line(line, commit_summary)
            
    if in_analyzing_changes:
        insert_commit(dbcon, commit_summary, changes)
        commit_num += 1
    
    return commit_num

def main(args):
    dbcon = pymysql.connect(host="localhost", user="giter", passwd="giter=01", db="gitwork", charset="utf8")

    for repository_name,git_path in Repositories.items():
        print('Processing %s'%repository_name)
        commits = get_git_commits(git_path)
        n = write_commit(dbcon, commits, repository_name)
        print('Total %d commits processed'%n)
    
    dbcon.close()

if __name__ == '__main__':
    # parse arguments
    args = parse_args()
    if args is None:
        exit()

    # main
    main(args)