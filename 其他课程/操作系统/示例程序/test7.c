/*pf.c*/
/*内核模块代码*/
#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/mm.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include <asm/uaccess.h>

struct proc_dir_entry *proc_pf;
struct proc_dir_entry *proc_pfcount;
extern unsigned long volatile pfcount;
static inline struct proc_dir_entry *proc_pf_create(const char* name,
  mode_t mode, read_proc_t *get_info)
{
    return create_proc_read_entry(name, mode, proc_pf, get_info, NULL);
}

int get_pfcount(char *buffer, char **start, off_t offset, int length, int *peof,
void *data)
{
    int len = 0;
    len = sprintf(buffer, "%ld \n", pfcount);
    return len;
}
static int pf_init(void)
{
    proc_pf = proc_mkdir("pf", 0);
    proc_pf_create("pfcount", 0, get_pfcount);
    return 0;
}

static void pf_exit(void)
{
    remove_proc_entry("pfcount", proc_pf);
    remove_proc_entry("pf", 0);
}

module_init(pf_init);
module_exit(pf_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Aron.t.wang");
