from src.updater.github_updater import GitHubUpdater

if __name__ == '__main__':
    u = GitHubUpdater('infinityambients-tech','mods-supermarket','0.0.0')
    print('OK', u.LOCK_FILE)
