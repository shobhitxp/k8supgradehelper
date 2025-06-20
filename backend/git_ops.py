from git import Repo
import os

def create_merge_request(repo_url: str, file_changes: dict, token: str):
    repo = Repo.clone_from(repo_url, "/tmp/kube-repo", branch="main")
    new_branch = "kube-api-upgrade"
    repo.git.checkout("-b", new_branch)
    
    for filepath, content in file_changes.items():
        full_path = os.path.join("/tmp/kube-repo", filepath)
        with open(full_path, "w") as f:
            f.write(content)
        repo.index.add([full_path])
    
    repo.index.commit("Automated upgrade of deprecated Kubernetes APIs")
    repo.remote().push(refspec=f"{new_branch}:{new_branch}")
    return f"MR pushed to branch: {new_branch}"

