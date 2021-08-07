import os,sys,zlib,copy
from collections import deque

def get_git():
	path = os.getcwd()
	for d in os.listdir(path):
		if d ==".git":
			p = path +"/.git"
			return p
		if path == "/": break
	sys.stderr("not inside a git repos")


def branches(path):
	branch = dict()
	path = path + "/refs/heads/"
	gpath = ".git/refs/heads/"
	lists = os.listdir(path)
	for i in lists:
		newpath = gpath+i
		if os.path.isdir(newpath):
			currentbranches(newpath,branch)
		else:
			branch_file = newpath
			f = open(branch_file,'r')
			branch[i] = f.readline().strip()
	return branch

def currentbranches(path, local):
	lists = os.listdir(path)
	for i in lists:
		newpath = path + "/" + i
		if os.path.isdir(newpath):
			currentbranches(newpath, local)
		else:
			local[path[16:] + "/" + i] = open(newpath,'r').readline().strip()

class CommitNode:
    def __init__(self, commit_hash):
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()

def topological_sort(commitgraph):
    result = []
    nochildren = deque() 
    copygraph = copy.deepcopy(commitgraph) 
    for ch in copygraph:
        if len(copygraph[ch].children) == 0:
            nochildren.append(ch)
    while len(nochildren) > 0:
        ch = nochildren.popleft()
        result.append(ch)
        for parenthash in list(copygraph[ch].parents):
            copygraph[ch].parents.remove(parenthash)
            copygraph[parenthash].children.remove(ch)
            if len(copygraph[parenthash].children) == 0:
                nochildren.append(parenthash)
    if len(result) < len(commitgraph):
        raise Exception("cycle detected")
    return result

def build_commit_graph(br, dirs):
	objectpath = dirs +"/objects/"
	commitnodes = dict()
	visited = set()
	s = br.values()
	stack = list(s)
	while stack:
		DFS(objectpath, commitnodes, stack[0],stack, visited)
		stack.pop(0)
	return commitnodes
		
def DFS(objectpath, commitn, hash, valuelist, visited):
	if hash not in visited:
		visited.add(hash)
		if hash not in commitn:
			commitn[hash] = CommitNode(hash)
		commitobject = commitn.get(hash)
		commitfile = objectpath + hash[:2]+"/"+hash[2:]
		objectp = open(commitfile,'rb').read()
		objectp = zlib.decompress(objectp).decode('UTF-8')
		if 'parent' in objectp:
			objectp = objectp.split('parent')
			for i in range(len(objectp)):
				if i != 0:
					commitobject.parents.add(objectp[i][1:41])
			for p in commitobject.parents:
				if p not in visited:
					valuelist.append(p)
				if p not in commitn:
					commitn[p] = CommitNode(p)
				commitn[p].children.add(hash) 

def topo_order_commits():
	path = get_git()
	branch = branches(path)
	commitgraph = build_commit_graph(branch,path)
	topo_ordered_commits = topological_sort(commitgraph)
	hbranches = dict()
	for branchname, ch in branch.items():
		if ch in hbranches.keys():
			hbranches[ch].append(branchname)
		else:
			hbranches[ch] = [branchname]
	print_ordered_commits_branch_names(commitgraph,topo_ordered_commits,hbranches)

def print_ordered_commits_branch_names(commitn,topo_ordered_commits,hbranches):
    jumped = False
    for i in range(len(topo_ordered_commits)):
        commit_hash = topo_ordered_commits[i]
        if jumped:
            jumped = False
            sticky_hash = ' '.join(commitn[commit_hash].children)
            print(f'={sticky_hash}')
        branches = sorted(hbranches[commit_hash]) if commit_hash in hbranches else []
        print(commit_hash + (' '+ ' '.join(branches) if branches else ''))
        if i+1 < len(topo_ordered_commits) and topo_ordered_commits[i+1] not in commitn[commit_hash].parents:
            jumped = True
            sticky_hash = ' '.join(commitn[commit_hash].parents)
            print(f'{sticky_hash}=\n')

if __name__ == '__main__':
    topo_order_commits()
