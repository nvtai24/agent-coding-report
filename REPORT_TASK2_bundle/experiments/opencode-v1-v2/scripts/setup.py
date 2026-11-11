"""Install the fixed Linux x64 lab binaries and generate isolated configs."""
import hashlib
import json
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from lab_env import LAB, ROOT, environment

manifest=json.loads((ROOT/'evidence/install-manifest.json').read_text())
LAB.mkdir(exist_ok=True)
for record in manifest['versions']:
    version=record['version']
    if record['major']==1:
        url=f'https://registry.npmjs.org/opencode-linux-x64/-/opencode-linux-x64-{version}.tgz'
    else:
        url=f'https://registry.npmjs.org/@opencode/cli-linux-x64/-/cli-linux-x64-{version}.tgz'
    archive=LAB/f'v{record["major"]}.tgz'
    if not archive.exists():
        subprocess.run(['curl','-fL','--retry','2','--max-time','180',url,'-o',str(archive)],check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=record['archiveSha256']:
        raise RuntimeError(f'Archive checksum mismatch for {version}')
    target=LAB/f'v{record["major"]}'
    target.mkdir(exist_ok=True)
    with tarfile.open(archive) as tar:tar.extractall(target,filter='data')

bun=LAB/'runtime/bun-linux-x64/bun'
if not bun.exists():
    archive=LAB/'bun.zip'
    subprocess.run(['curl','-fL','--retry','2','--max-time','180',
        'https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-linux-x64.zip','-o',str(archive)],check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!='bf8ccbfb2b0b80159e0f9a6d15c55317add8077534dbc6130a3edb52fccb395c':
        raise RuntimeError('Bun checksum mismatch')
    with zipfile.ZipFile(archive) as source:source.extractall(LAB/'runtime')
    bun.chmod(0o755)
subprocess.run([str(bun),'install','--frozen-lockfile'],cwd=ROOT,check=True)
for version in [1,2]:
    environment(version)
    project=LAB/f'project-v{version}'
    project.mkdir(exist_ok=True)
    (project/'README.md').write_text('# OpenCode migration lab\nMarker: MIGRATION-2026\n')
    subprocess.run(['git','init','-q',str(project)],check=True)
    rules={'*':'allow','printf LAB_ASK':'ask','printf LAB_DENY':'deny'}
    config={'model':'opencode/minimax-m3.1-flash-free'}
    if version==1:
        config.update(plugin=[str(ROOT/'plugins/v1/index.ts')],permission={'bash':rules})
    else:
        config.update(plugins=[str(ROOT/'plugins/v2')],permissions=[{'action':'shell','resource':key,'effect':value} for key,value in rules.items()])
    text=json.dumps(config,indent=2)+'\n'
    (ROOT/'configs'/f'v{version}.json').write_text(text)
    (project/'opencode.json').write_text(text)

# Reuse locally installed dependencies for V1's per-config plugin environment.
config=LAB/'home-v1/config/opencode'
config.mkdir(parents=True,exist_ok=True)
link=config/'node_modules'
if not link.exists():link.symlink_to(ROOT/'node_modules',target_is_directory=True)
package={'name':'opencode-v1-lab-config','private':True,'dependencies':{'@opencode-ai/plugin':'1.19.5'}}
(config/'package.json').write_text(json.dumps(package))
lock={'name':package['name'],'lockfileVersion':3,'requires':True,'packages':{'':package}}
for parent in (ROOT/'node_modules').iterdir():
    paths=list(parent.iterdir()) if parent.name.startswith('@') else [parent]
    for dependency in paths:
        file=dependency/'package.json'
        if not file.exists():continue
        data=json.loads(file.read_text())
        lock['packages']['node_modules/'+data['name']]={key:data[key] for key in ['version','dependencies','peerDependencies','optionalDependencies'] if key in data}
(config/'package-lock.json').write_text(json.dumps(lock))
print('Installed OpenCode 1.19.5 and 2.2.7 with isolated paths under /tmp/opencode-lab.')
