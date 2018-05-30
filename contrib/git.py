import argparse
import os
import subprocess

"""parsing and configuration"""
def parse_args():
    desc = "Retrieve commits from git"
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--git_path', type=str, default='C:\\Users\\geesi\\Desktop\\BQ\\mall-root',
                        help='Git directory path')

    return parser.parse_args()


def get_git_commits(git_path):
    os.chdir(git_path)
    result = subprocess.run(['git','log', 'master', 
                            '--pretty=format:"#%H,%cn,%ce,%ci"', 
                            '--numstat', '--no-merges', '--first-parent'], stdout=subprocess.PIPE)
    return result.stdout

def main(args):
    #git log --pretty=format:"!%H,%cn,%ce,%ci" --numstat
    commits = get_git_commits(args.git_path)

    print(len(commits))

if __name__ == '__main__':
    # parse arguments
    args = parse_args()
    if args is None:
        exit()

    # main
    main(args)
