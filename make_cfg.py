cfg_template = r"""[18pfd_{i:02d}]
list = 18pfd_wk{i:02d}.txt
folder = repository\wk{i:02d}
count_commits = True
run_all = True
pound_count = True
after = 2018-08-27 12:52
"""
for i in range(5, 10+1):
    if 8 != i:
        print(cfg_template.format(**{'i': i}))
