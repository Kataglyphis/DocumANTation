# Computer Programming - An Introduction

Inside every computer, there’s a special set of instructions that makes a computer to work, is called a computer program. It’s the essential life force that transforms computer hardware into a functional device. To help you understand this concept, think of a computer as a piano, an instrument that remains silent without a skilled musician.

However, computers, by their nature, are exceptionally proficient at executing some basic operations, such as addition and division, etc. A computer is performing these operations at lightning speed and with flawless accuracy.

Now, taking into a practical scenario. Imagine you’re on a long road trip, and you want to calculate your average speed. The distance you’ve traveled and the time it took to reach your destination, but here’s the problem, that  computers don’t intuitively understand these concepts as a human you do. Therefore, you need to provide precise instructions to the computer, as instructing it to:

- Accept a numerical value representing the distance.
- Accept a numerical value representing the travel time.
- Divide the distance by the time and store the result in memory.
- Display the result (average speed) in a human-readable format.

When combined, all these four apparently simple actions make a computer program. Even though these actions are different from that of what a computer naturally understands, they can be translated into a language that the computer can understand.

## Natural Languages vs. Programming Languages

Human language serve as tools for expressing intentions and transferring knowledge. Even though some languages require no spoken or written words, as they rely on gestures or body language, while others, like our mother tongue, enable us to convey our thoughts and reflect reality. Computers have their own language, known as machine language, which is complex and challenging for humans to understand fully.

It’s important to note that even the most advanced computers lack true intelligence, because they responded solely to a predefined set of known commands, often very basic ones. Think of it as computers following orders like “take this number, divide it by another, and save the result.” This set of known commands is referred to as an instruction list or `IL`.

> *Note*: machine languages are also created by humans.

### The anatomy of a language

Every language, whether natural or machine-based, comprises the following key elements:


- ***Alphabet:*** A set of symbols used to construct words within the language.
- ***Lexis (Dictionary):*** A collection of words and their meanings within the language.
- ***Syntax:*** A set of rules governing the structure of sentences and phrases.
- ***Semantics:*** A set of rules determining the meaning of a given phrase or sentence.

In the case of machine language, the `IL` serves as the alphabet (`zeroes` and `ones`). However, humans require a more expressive language to write programs—one that computers can execute. These languages, often known as high-level programming languages, share similarities with natural languages. They have symbols, words, and conventions that humans can understand, high-level languages empower humans to issue commands to computers.

A program written in a high-level programming language is referred to as `source code`, and the file containing this source code is known as a `source file`.

### Compilation vs. interpretation

Computer programming involves composing elements of a selected programming language in a manner that achieves the desired outcome. This outcome has depending on the programmer’s imagination, knowledge, and experience.

There are two primary methods for translating a program from a high-level programming language into machine language:

1. ***Compilation:*** The source program is translated once to create a file containing machine code. This resulting file can be distributed globally, and the program responsible for this translation is known as a `compiler`.

2. ***Interpretation:*** The source program is translated each time it needs to run. The program performing this kind of transformation is an `interpreter`, as it interprets the code every time it’s executed. This also implies that you can’t distribute the source code as-is; the end-user also requires the interpreter to execute it.

#### Compilation — advantages and disadvantages

- **Advantages**:
    - Executed code is typically faster.
    - Only the user needs the compiler; the end-user can use the code without it.
    - The translated code is stored in machine language, keeping it secure.

- **Disadvantages**:
    - Compilation is a time-consuming process; you can’t run your code immediately after making changes.
    - You require a compiler for each hardware platform you want your code to run on.

#### Interpretation — advantages and disadvantages

- **Advantages**:
    - You can run the code as soon as you finish writing it; no need for additional translation phases.
    - The code is stored in a programming language, not machine language. It can run on computers with different architectures without separate compilation.

- **Disadvantages**:
    - Interpretation doesn’t result in high-speed execution; your code shares resources with the interpreter.
    - Both you and the end-user require the interpreter to run your code.

Python falls into the category of interpreted languages. To program in Python, you’ll need a Python interpreter. Without it, you won’t be able to execute your code. The best part is that Python is free, making it one of its most significant advantages. Languages designed for interpretation are often referred to as scripting languages, and the source programs written in them are called scripts.

## Understanding Python Language

Python is a widely-used, interpreted, object-oriented, high-level programming language with dynamic semantics. It’s employed for general-purpose programming and is known for its versatility. The name “Python” comes from an old BBC television comedy sketch series called Monty Python’s Flying Circus.

Python’s creation is credited to *Guido van Rossum*, born in `1956` in Haarlem, the Netherlands. While Python’s popularity has grown worldwide, it’s essential to acknowledge that it all started with Guido’s vision.

In `1999`, *Guido van Rossum* outlined his goals for Python:

- Create an easy, intuitive, and powerful language.
- Keep it open source.
- Make it understandable, like plain English.
- Ensure it’s suitable for everyday tasks, allowing for short development times.
- Python has matured and gained trust in the programming world. It’s not just a flash in the pan but a bright star in the programming firmament.

### What sets Python apart?

There are numerous reasons why Python stands out, as we’ve mentioned earlier. Let’s summarize them practically:

- Easy to Learn: Learning Python takes less time compared to many other languages, allowing you to start programming quickly.
- Easy to Teach: Teaching Python is more straightforward, focusing on programming techniques rather than complex language intricacies.
- Easy to Use: Python often lets you write code faster when creating new software.
- Easy to Understand: Python code is generally easier to comprehend, making it simpler to read and maintain.
- Easy to Obtain, Install, and Deploy: Python is free, open-source, and cross-platform, making it accessible to all.

It’s worth noting that Python is not the only solution in the programming landscape.

### Python’s competitors

This is inline latex: $f(x) = \sum_{i=0}^{n} \frac{a_i}{1+x}$
latex: $c = \pm\sqrt{a^2 + b^2}$
This is block level latex:

This is inline latex with displayMode: $$f(x) = \sum_{i=0}^{n} \frac{a_i}{1+x}$$ This is inline latex with displayMode: $$f(x) = \sum_{i=0}^{n} \frac{a_i}{1+x}$$ This is inline latex with displayMode: $$f(x) = \sum_{i=0}^{n} \frac{a_i}{1+x}$$

**The Cauchy-Schwarz Inequality**

```math
  \left( \sum_{k=1}^n a_k b_k \right)^2 \leq \left( \sum_{k=1}^n a_k^2 \right) \left( \sum_{k=1}^n b_k^2 \right)
```


```c
/* SPDX-License-Identifier: GPL-2.0 */
#ifndef __CGROUP_INTERNAL_H
#define __CGROUP_INTERNAL_H

#include <linux/cgroup.h>
#include <linux/kernfs.h>
#include <linux/workqueue.h>
#include <linux/list.h>
#include <linux/refcount.h>
#include <linux/fs_parser.h>

#define TRACE_CGROUP_PATH_LEN 1024
extern spinlock_t trace_cgroup_path_lock;
extern char trace_cgroup_path[TRACE_CGROUP_PATH_LEN];
extern void __init enable_debug_cgroup(void);

/*
 * cgroup_path() takes a spin lock. It is good practice not to take
 * spin locks within trace point handlers, as they are mostly hidden
 * from normal view. As cgroup_path() can take the kernfs_rename_lock
 * spin lock, it is best to not call that function from the trace event
 * handler.
 *
 * Note: trace_cgroup_##type##_enabled() is a static branch that will only
 *       be set when the trace event is enabled.
 */
#define TRACE_CGROUP_PATH(type, cgrp, ...)				\
	do {								\
		if (trace_cgroup_##type##_enabled()) {			\
			unsigned long flags;				\
			spin_lock_irqsave(&trace_cgroup_path_lock,	\
					  flags);			\
			cgroup_path(cgrp, trace_cgroup_path,		\
				    TRACE_CGROUP_PATH_LEN);		\
			trace_cgroup_##type(cgrp, trace_cgroup_path,	\
					    ##__VA_ARGS__);		\
			spin_unlock_irqrestore(&trace_cgroup_path_lock, \
					       flags);			\
		}							\
	} while (0)

/*
 * The cgroup filesystem superblock creation/mount context.
 */
struct cgroup_fs_context {
	struct kernfs_fs_context kfc;
	struct cgroup_root	*root;
	struct cgroup_namespace	*ns;
	unsigned int	flags;			/* CGRP_ROOT_* flags */

	/* cgroup1 bits */
	bool		cpuset_clone_children;
	bool		none;			/* User explicitly requested empty subsystem */
	bool		all_ss;			/* Seen 'all' option */
	u16		subsys_mask;		/* Selected subsystems */
	char		*name;			/* Hierarchy name */
	char		*release_agent;		/* Path for release notifications */
};

static inline struct cgroup_fs_context *cgroup_fc2context(struct fs_context *fc)
{
	struct kernfs_fs_context *kfc = fc->fs_private;

	return container_of(kfc, struct cgroup_fs_context, kfc);
}

struct cgroup_pidlist;

struct cgroup_file_ctx {
	struct cgroup_namespace	*ns;

	struct {
		void			*trigger;
	} psi;

	struct {
		bool			started;
		struct css_task_iter	iter;
	} procs;

	struct {
		struct cgroup_pidlist	*pidlist;
	} procs1;
};

/*
 * A cgroup can be associated with multiple css_sets as different tasks may
 * belong to different cgroups on different hierarchies.  In the other
 * direction, a css_set is naturally associated with multiple cgroups.
 * This M:N relationship is represented by the following link structure
 * which exists for each association and allows traversing the associations
 * from both sides.
 */
struct cgrp_cset_link {
	/* the cgroup and css_set this link associates */
	struct cgroup		*cgrp;
	struct css_set		*cset;

	/* list of cgrp_cset_links anchored at cgrp->cset_links */
	struct list_head	cset_link;

	/* list of cgrp_cset_links anchored at css_set->cgrp_links */
	struct list_head	cgrp_link;
};

/* used to track tasks and csets during migration */
struct cgroup_taskset {
	/* the src and dst cset list running through cset->mg_node */
	struct list_head	src_csets;
	struct list_head	dst_csets;

	/* the number of tasks in the set */
	int			nr_tasks;

	/* the subsys currently being processed */
	int			ssid;

	/*
	 * Fields for cgroup_taskset_*() iteration.
	 *
	 * Before migration is committed, the target migration tasks are on
	 * ->mg_tasks of the csets on ->src_csets.  After, on ->mg_tasks of
	 * the csets on ->dst_csets.  ->csets point to either ->src_csets
	 * or ->dst_csets depending on whether migration is committed.
	 *
	 * ->cur_csets and ->cur_task point to the current task position
	 * during iteration.
	 */
	struct list_head	*csets;
	struct css_set		*cur_cset;
	struct task_struct	*cur_task;
};

/* migration context also tracks preloading */
struct cgroup_mgctx {
	/*
	 * Preloaded source and destination csets.  Used to guarantee
	 * atomic success or failure on actual migration.
	 */
	struct list_head	preloaded_src_csets;
	struct list_head	preloaded_dst_csets;

	/* tasks and csets to migrate */
	struct cgroup_taskset	tset;

	/* subsystems affected by migration */
	u16			ss_mask;
};

#define CGROUP_TASKSET_INIT(tset)						\
{										\
	.src_csets		= LIST_HEAD_INIT(tset.src_csets),		\
	.dst_csets		= LIST_HEAD_INIT(tset.dst_csets),		\
	.csets			= &tset.src_csets,				\
}

#define CGROUP_MGCTX_INIT(name)							\
{										\
	LIST_HEAD_INIT(name.preloaded_src_csets),				\
	LIST_HEAD_INIT(name.preloaded_dst_csets),				\
	CGROUP_TASKSET_INIT(name.tset),						\
}

#define DEFINE_CGROUP_MGCTX(name)						\
	struct cgroup_mgctx name = CGROUP_MGCTX_INIT(name)

extern struct cgroup_subsys *cgroup_subsys[];
extern struct list_head cgroup_roots;

/* iterate across the hierarchies */
#define for_each_root(root)						\
	list_for_each_entry_rcu((root), &cgroup_roots, root_list,	\
				lockdep_is_held(&cgroup_mutex))

/**
 * for_each_subsys - iterate all enabled cgroup subsystems
 * @ss: the iteration cursor
 * @ssid: the index of @ss, CGROUP_SUBSYS_COUNT after reaching the end
 */
#define for_each_subsys(ss, ssid)					\
	for ((ssid) = 0; (ssid) < CGROUP_SUBSYS_COUNT &&		\
	     (((ss) = cgroup_subsys[ssid]) || true); (ssid)++)

static inline bool cgroup_is_dead(const struct cgroup *cgrp)
{
	return !(cgrp->self.flags & CSS_ONLINE);
}

static inline bool notify_on_release(const struct cgroup *cgrp)
{
	return test_bit(CGRP_NOTIFY_ON_RELEASE, &cgrp->flags);
}

void put_css_set_locked(struct css_set *cset);

static inline void put_css_set(struct css_set *cset)
{
	unsigned long flags;

	/*
	 * Ensure that the refcount doesn't hit zero while any readers
	 * can see it. Similar to atomic_dec_and_lock(), but for an
	 * rwlock
	 */
	if (refcount_dec_not_one(&cset->refcount))
		return;

	spin_lock_irqsave(&css_set_lock, flags);
	put_css_set_locked(cset);
	spin_unlock_irqrestore(&css_set_lock, flags);
}

/*
 * refcounted get/put for css_set objects
 */
static inline void get_css_set(struct css_set *cset)
{
	refcount_inc(&cset->refcount);
}

bool cgroup_ssid_enabled(int ssid);
bool cgroup_on_dfl(const struct cgroup *cgrp);

struct cgroup_root *cgroup_root_from_kf(struct kernfs_root *kf_root);
struct cgroup *task_cgroup_from_root(struct task_struct *task,
				     struct cgroup_root *root);
struct cgroup *cgroup_kn_lock_live(struct kernfs_node *kn, bool drain_offline);
void cgroup_kn_unlock(struct kernfs_node *kn);
int cgroup_path_ns_locked(struct cgroup *cgrp, char *buf, size_t buflen,
			  struct cgroup_namespace *ns);

void cgroup_favor_dynmods(struct cgroup_root *root, bool favor);
void cgroup_free_root(struct cgroup_root *root);
void init_cgroup_root(struct cgroup_fs_context *ctx);
int cgroup_setup_root(struct cgroup_root *root, u16 ss_mask);
int rebind_subsystems(struct cgroup_root *dst_root, u16 ss_mask);
int cgroup_do_get_tree(struct fs_context *fc);

int cgroup_migrate_vet_dst(struct cgroup *dst_cgrp);
void cgroup_migrate_finish(struct cgroup_mgctx *mgctx);
void cgroup_migrate_add_src(struct css_set *src_cset, struct cgroup *dst_cgrp,
			    struct cgroup_mgctx *mgctx);
int cgroup_migrate_prepare_dst(struct cgroup_mgctx *mgctx);
int cgroup_migrate(struct task_struct *leader, bool threadgroup,
		   struct cgroup_mgctx *mgctx);

int cgroup_attach_task(struct cgroup *dst_cgrp, struct task_struct *leader,
		       bool threadgroup);
void cgroup_attach_lock(bool lock_threadgroup);
void cgroup_attach_unlock(bool lock_threadgroup);
struct task_struct *cgroup_procs_write_start(char *buf, bool threadgroup,
					     bool *locked)
	__acquires(&cgroup_threadgroup_rwsem);
void cgroup_procs_write_finish(struct task_struct *task, bool locked)
	__releases(&cgroup_threadgroup_rwsem);

void cgroup_lock_and_drain_offline(struct cgroup *cgrp);

int cgroup_mkdir(struct kernfs_node *parent_kn, const char *name, umode_t mode);
int cgroup_rmdir(struct kernfs_node *kn);
int cgroup_show_path(struct seq_file *sf, struct kernfs_node *kf_node,
		     struct kernfs_root *kf_root);

int __cgroup_task_count(const struct cgroup *cgrp);
int cgroup_task_count(const struct cgroup *cgrp);

/*
 * rstat.c
 */
int cgroup_rstat_init(struct cgroup *cgrp);
void cgroup_rstat_exit(struct cgroup *cgrp);
void cgroup_rstat_boot(void);
void cgroup_base_stat_cputime_show(struct seq_file *seq);

/*
 * namespace.c
 */
extern const struct proc_ns_operations cgroupns_operations;

/*
 * cgroup-v1.c
 */
extern struct cftype cgroup1_base_files[];
extern struct kernfs_syscall_ops cgroup1_kf_syscall_ops;
extern const struct fs_parameter_spec cgroup1_fs_parameters[];

int proc_cgroupstats_show(struct seq_file *m, void *v);
bool cgroup1_ssid_disabled(int ssid);
void cgroup1_pidlist_destroy_all(struct cgroup *cgrp);
void cgroup1_release_agent(struct work_struct *work);
void cgroup1_check_for_release(struct cgroup *cgrp);
int cgroup1_parse_param(struct fs_context *fc, struct fs_parameter *param);
int cgroup1_get_tree(struct fs_context *fc);
int cgroup1_reconfigure(struct fs_context *ctx);

#endif /* __CGROUP_INTERNAL_H */
```