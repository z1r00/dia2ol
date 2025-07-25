# dia2ol v0.1

`dia2ol`将二进制程序自动diff后转为可读的diff代码，并在web端显示diff代码

生成的diff会保存到gist中，默认以`secret`方式存放

## 安装必要的环境

### 一、安装GitHub官方命令行工具

#### Mac OS

```
brew install gh
```

#### Windows

访问https://cli.github.com/，下载并执行安装

#### Ubuntu

```
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
	&& sudo mkdir -p -m 755 /etc/apt/keyrings \
	&& wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y
```

更多安装信息参考https://github.com/cli/cli/tree/v2.63.2?tab=readme-ov-file#installation

## 运行

### 一、登陆gist

根据下面的步骤执行，正常使用https就可以成功

```
gh auth login
? Where do you use GitHub? GitHub.com
? What is your preferred protocol for Git operations on this host? HTTPS
? Authenticate Git with your GitHub credentials? Yes
? How would you like to authenticate GitHub CLI? Login with a web browser

! First copy your one-time code: XXXX-XXXX
Press Enter to open https://github.com/login/device in your browser...
```

回车后即可进入gist认证，认证成功结果如下

```
✓ Authentication complete.
- gh config set -h github.com git_protocol https
✓ Configured git protocol
✓ Logged in as z1r00
! You were already logged in to this account
```

更多帮助信息：https://cli.github.com/manual/gh_auth_login

### 二、设置setting.cfg

#### ida_path（必须）

path中设置idat64的执行路径

```
[ida_path]
path=/Applications/IDA Professional 9.0.app/Contents/MacOS/idat64
```

#### desc

desc中设置gist仓库描述

```
[gist]
desc=BinaryDiff
```

### 三、运行

需要设置`--old_file`和`--new_file`参数或者`--old_dir`和`--new_dir`参数，`--old_file`参数是patch前的程序、`--new_file`是patch后的程序，`--old_dir`参数是patch前的程序所在目录、`--new_dir`是patch后的程序所在目录，运行之后等待即可，正常用--new_dir和--old_dir（可以多个二进制文件同时对比）

最后出现`[+] open: https://www.z1r0.top/binarydiff/?`则成功

```
usage: dia2ol.py [-h] [--old_file OLD_FILE] [--new_file NEW_FILE] [--old_dir OLD_DIR] [--new_dir NEW_DIR] [--local]

Diff old_file and new_file.

options:
  -h, --help           show this help message and exit
  --old_file OLD_FILE  The old file
  --new_file NEW_FILE  The new file
  --old_dir OLD_DIR    The old directory
  --new_dir NEW_DIR    The new directory
  --local              Local Diff
```

#### 用法样例

下载一个patch前的程序和一个patch后的程序

```
mkdir old && wget https://msdl.microsoft.com/download/symbols/afd.sys/0C5C6994A8000/afd.sys -O old/afd.sys
mkdir new && wget https://msdl.microsoft.com/download/symbols/afd.sys/50989142A9000/afd.sys -O new/afd.sys
```

执行脚本

```
python3 /path/to/dia2ol.py --old_dir old --new_dir new
```

结果回显

```
olddir:/mypath/old ; newdir:/mypath/new
{'afd.sys'}
/mypath/old/afd.sys(binary) to /mypath/old/afd.sys.old.sqlite
[*] wattings
[OK] patch database blacklists
[OK] patch http_request
[OK] patch lumina
[OK] patch 23945/udp
BinDiff 7 (@377901646, Jun  7 2021), (c)2004-2011 zynamics GmbH, (c)2011-2021 Google LLC.
BinExport 12 (@377901646, Jun  7 2021), (c)2004-2011 zynamics GmbH, (c)2011-2021 Google LLC.
/Applications/IDA Pro 8.3/ida64.app/Contents/MacOS/plugins/lighthouse_plugin.py: undefined function __plugins__lighthouse_plugin.PLUGIN_ENTRY

/mypath/new/afd.sys(binary) to /mypath/new/afd.sys.new.sqlite
[*] watting
[OK] patch database blacklist
[OK] patch http_request
[OK] patch lumina
[OK] patch 23945/udp
BinDiff 7 (@377901646, Jun  7 2021), (c)2004-2011 zynamics GmbH, (c)2011-2021 Google LLC.
BinExport 12 (@377901646, Jun  7 2021), (c)2004-2011 zynamics GmbH, (c)2011-2021 Google LLC.
/Applications/IDA Pro 8.3/ida64.app/Contents/MacOS/plugins/lighthouse_plugin.py: undefined function __plugins__lighthouse_plugin.PLUGIN_ENTRY

['/Library/Frameworks/Python.framework/Versions/3.11/bin/python3', '/path/dia2ol/diaphora/diaphora.py', '/mypath/old/afd.sys.old.sqlite', '/mypath/new/afd.sys.new.sqlite', '-o', '/mypath/new/afd.sys.new.sqlite.output.sqlite']
WARNING: Python library 'cdifflib' not found. Installing it will significantly improve text diffing performance.
INFO: Alternatively, you can silence this warning by changing the value of SHOW_IMPORT_WARNINGS in diaphora_config.py.
Both numpy and Scikit Learn are needed to use local models.
Both numpy and Scikit Learn are needed to use local models.
Error loading project specific Python script: module 'importlib' has no attribute 'util'

[+] Sqlite Saved
[+] partialDiff
1c00798fc | 1c007a8fc | WPP_SF_dd | WPP_SF_dd
1c00799f8 | 1c007a9f8 | WPP_SF_ll | WPP_SF_ll
1c00631f4 | 1c0063624 | AfdTcp6RoutingQuery | AfdTcp6RoutingQuery
1c00796d8 | 1c007a6d8 | WPP_SF_Sll | WPP_SF_Sll
1c001ffb2 | 1c00207f2 | AfdHasHeldPacketsFromNic | AfdHasHeldPacketsFromNic
1c0087a3c | 1c0088f18 | AfdCreateSecurityDescriptor | AfdCreateSecurityDescriptor
1c0079658 | 1c007a658 | WPP_SF_SlP | WPP_SF_SlP
1c006f92c | 1c006fd5c | AfdNotifyRemoveIoCompletion | AfdNotifyRemoveIoCompletion
1c00704ec | 1c007092c | AfdTcpRoutingQuery | AfdTcpRoutingQuery
1c0079a94 | 1c007aa94 | WPP_SF_qqll | WPP_SF_qqll
1c0038630 | 1c0038eb0 | AfdCancelAddressListChange | AfdCancelAddressListChange
1c00392f0 | 1c0039b70 | AfdRoutingInterfaceChange | AfdRoutingInterfaceChange
1c0063010 | 1c0063440 | AfdRoutingInterfaceQuery | AfdRoutingInterfaceQuery
1c0064820 | 1c0064c50 | AfdAddressListQuery | AfdAddressListQuery
1c0065c20 | 1c0066050 | AfdCommonDelAddressHandler | AfdCommonDelAddressHandler
1c006636c | 1c00667f0 | AfdCommonAddAddressHandler | AfdCommonAddAddressHandler
1c0066664 | 1c0066ae8 | AfdNotifyIPAvailabilityConsumers | AfdNotifyIPAvailabilityConsumers
1c00681e4 | 1c0068664 | AfdInitializeAddressList | AfdInitializeAddressList
1c006e0f0 | 1c006e510 | AfdReadVolatileParameters | AfdReadVolatileParameters
1c006e250 | 1c006e670 | AfdUnload | AfdUnload
1c0079590 | 1c007a590 | WPP_SF_SLsL | WPP_SF_SLsL
1c0079944 | 1c007a944 | WPP_SF_dldZ | WPP_SF_dldZ
1c0087078 | 1c00881b0 | DriverEntry | DriverEntry
1c0065f00 | 1c0066330 | AfdNsiAddressChangeEventAtPassive | AfdNsiAddressChangeEventAtPassive
[+] multimatchDiff
[+] Newly added functions
1c001c348 | wil_details_FeatureDescriptors_SkipPadding
1c001c370 | Feature_Servicing_SiloCrashFixinAFD__private_IsEnabled
1c001c3c0 | wil_details_FeatureReporting_IncrementOpportunityInCache
1c001c4b4 | wil_details_FeatureReporting_IncrementUsageInCache
1c001c5ac | wil_details_FeatureReporting_RecordUsageInCache
1c001c700 | wil_details_FeatureReporting_ReportUsageToService
1c001c784 | wil_details_FeatureReporting_ReportUsageToServiceDirect
1c001c880 | wil_details_FeatureStateCache_GetCachedFeatureEnabledState
1c001c8b4 | wil_details_FeatureStateCache_ReevaluateCachedFeatureEnabledState
1c001c9b4 | wil_details_GetCurrentFeatureEnabledState
1c001cadc | wil_details_MapReportingKind
1c0032c70 | AfdAllocatePoolPriority
1c0063008 | wil_UninitializeFeatureStaging
1c0063038 | wil_details_BuildFeatureStateCacheFromQueryResults
1c00630ac | wil_details_EvaluateFeatureDependencies
1c0063158 | wil_details_EvaluateFeatureDependencies_GetCachedFeatureEnabledState
1c006318c | wil_details_EvaluateFeatureDependencies_ReevaluateCachedFeatureEnabledState
1c0063240 | wil_details_OnFeatureConfigurationChange
1c006325c | wil_details_RegisterFeatureStagingChangeNotification
1c00632c0 | wil_details_UpdateFeatureConfiguredStates
1c0063374 | wil_RtlStagingConfig_QueryFeatureState
1c0088078 | wil_InitializeFeatureStaging
1c00880bc | wil_details_PopulateInitialConfiguredFeatureStates
[+] Subtracting function
[*] Upload Gist
1ffe49c8c83e09ac5c8e7d554b3e19df	CVE-2020-17001	2 files	secret	2025-02-25T07:17:52Z
[-] not in gist
[*] Gist Creat
[+] Gist id = 03cb49cef029896af15779aeff5cca83

[+] open: https://www.z1r0.top/binarydiff/?03cb49cef029896af15779aeff5cca83/afd.sys.old.sqlite-afd.sys.new.sqlite.diff
```

会显示出对应函数修改后的函数名，以及新增函数，并且会在自己的gist仓库中会创建一个隐私仓库（默认）用来存储diff代码
直接访问https://www.z1r0.top/binarydiff/?03cb49cef029896af15779aeff5cca83/afd.sys.old.sqlite-afd.sys.new.sqlite.diff
就可以看见diff代码

## 出现的问题
1. windows平台上可能出现系统找不到指定文件，此时需要进入当前的python lib，将init中的shell=False改为shell=True

## To Do
- [+] 多个二进制文件同时diff(完成)
- [+] 本地diff，vsocde直接进行比较（完成）
- [-] 优化速度
- [-] 本地diff，生成本地离线Web