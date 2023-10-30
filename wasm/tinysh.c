#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>

#define MAXARGS 64

struct cmd {
  char *argv[MAXARGS];
  char *eargv[MAXARGS];
  int argc;
};

struct cmdimpl {
  const char *name;
  void (*run)(struct cmd*);
};

static void
cmd_echo(struct cmd *cmd) {
  for (int i = 1; i < cmd->argc; i++) {
    printf("%s ", cmd->argv[i]);
  }
  printf("\n");
}

static void
cmd_pwd(struct cmd *cmd) {
  char buf[1024];
  char *res;
  res = getcwd(buf, sizeof(buf));
  if (!res) {
    fprintf(stderr, "cannot getcwd\n");
  } else {
    printf("%s\n", res);
  }
}

static void
cmd_cd(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: cd dirname\n");
    return;
  }

  int r = chdir(cmd->argv[1]);
  if (r < 0) {
    perror("chdir");
  }
}

static void
ls_entry(char *de_name, char *dirname, int longflag) {
  if (longflag) {
    char pn[256];
    snprintf(pn, sizeof(pn), "%s/%s", dirname, de_name);
    struct stat st;
    int r = lstat(pn, &st);

    char *type = "?";
    char extra[256];
    size_t len = 0;
    extra[0] = '\0';

    if (r < 0) {
      // perror("stat");
    } else {
      len = st.st_size;
      if (S_ISREG(st.st_mode)) {
        type = "-";
      } else if (S_ISDIR(st.st_mode)) {
        type = "d";
      } else if (S_ISLNK(st.st_mode)) {
        type = "l";
        char target[128];
        int r = readlink(pn, target, sizeof(target));
        if (r < 0) {
          perror("readlink");
        } else {
          if (r < sizeof(target)) {
            target[r] = '\0';
            snprintf(extra, sizeof(extra), " -> %s", target);
          }
        }
      }
    }
    printf("%s %8lld %s%s\n", type, st.st_size, de_name, extra);
  } else {
    printf("%s\n", de_name);
  }
}

static void
cmd_ls(struct cmd *cmd) {
  int argc = cmd->argc - 1;
  char **argv = &cmd->argv[1];
  int longflag = 0;
  while (argc > 0) {
    if (*argv[0] == '-') {
      if (!strcmp(*argv, "-l")) {
        longflag = 1;
        argc--;
        argv++;
      } else {
        goto usage;
      }
    } else {
      break;
    }
  }

  char *pathname;
  if (argc == 0) {
    pathname = ".";
  } else if (argc == 1) {
    pathname = *argv;
  } else {
    goto usage;
  }

  struct stat st;
  int r = lstat(pathname, &st);
  if (r < 0) {
    perror("lstat");
    return;
  }

  if (!S_ISDIR(st.st_mode)) {
    ls_entry(pathname, ".", longflag);
    return;
  }

  DIR *d = opendir(pathname);
  if (!d) {
    perror("opendir");
    return;
  }

  for (;;) {
    struct dirent *de = readdir(d);
    if (!de) {
      break;
    }
    ls_entry(de->d_name, pathname, longflag);
  }

  closedir(d);
  return;

usage:
  fprintf(stderr, "usage: ls [-l] [pathname]\n");
  return;
}

static void
cmd_cat(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: cat filename\n");
    return;
  }

  int fd = open(cmd->argv[1], O_RDONLY);
  if (fd < 0) {
    perror("open");
    return;
  }

  for (;;) {
    char buf[1024];
    int cc = read(fd, buf, sizeof(buf));
    if (cc == 0) {
      break;
    }
    if (cc < 0) {
      perror("read");
      return;
    }
    write(1, buf, cc);
  }

  close(fd);
}

static void
cmd_mkdir(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: mkdir dirname\n");
    return;
  }

  int r = mkdir(cmd->argv[1], 0777);
  if (r < 0) {
    perror("mkdir");
  }
}

static void
cmd_rmdir(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: rmdir dirname\n");
    return;
  }

  int r = rmdir(cmd->argv[1]);
  if (r < 0) {
    perror("rmdir");
  }
}

static void
cmd_rm(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: rm pathname\n");
    return;
  }

  int r = unlink(cmd->argv[1]);
  if (r < 0) {
    perror("unlink");
  }
}

static void
cmd_touch(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: touch pathname\n");
    return;
  }

  int fd = open(cmd->argv[1], O_RDWR | O_CREAT, 0666);
  if (fd < 0) {
    perror("open");
  }

  close(fd);
}

static void
cmd_mv(struct cmd *cmd) {
  if (cmd->argc != 3) {
    fprintf(stderr, "usage: mv src dst\n");
    return;
  }

  int r = rename(cmd->argv[1], cmd->argv[2]);
  if (r < 0) {
    perror("rename");
  }
}

static void
cmd_ln(struct cmd *cmd) {
  if (cmd->argc != 4 || strcmp(cmd->argv[1], "-s")) {
    fprintf(stderr, "usage: ln -s target linkfile\n");
    return;
  }

  int r = symlink(cmd->argv[2], cmd->argv[3]);
  if (r < 0) {
    perror("symlink");
  }
}

static void
cmd_cp(struct cmd *cmd) {
  if (cmd->argc != 3) {
    fprintf(stderr, "usage: cp src dst\n");
    return;
  }

  int src = open(cmd->argv[1], O_RDONLY);
  if (src < 0) {
    perror("open src");
    return;
  }

  int dst = open(cmd->argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0666);
  if (dst < 0) {
    perror("open dst");
    return;
  }

  for (;;) {
    char buf[1024];
    size_t cc = read(src, buf, sizeof(buf));
    if (cc < 0) {
      perror("read");
      return;
    }

    if (cc == 0) {
      break;
    }

    size_t ncc = write(dst, buf, cc);
    if (ncc < 0) {
      perror("write");
      return;
    }

    if (ncc != cc) {
      fprintf(stderr, "cp: short write\n");
      return;
    }
  }

  close(src);
  close(dst);
}

static void
cmd_fd_list(struct cmd *cmd) {
  for (int i = 0; i < 128; i++) {
    struct stat st;
    int r = fstat(i, &st);
    if (r < 0) {
      continue;
    }

    char *type = "unknown";
    if (S_ISREG(st.st_mode)) {
      type = "file";
    } else if (S_ISDIR(st.st_mode)) {
      type = "dir";
    }
    printf("%3d: type %s\n", i, type);
  }
}

static void
cmd_fd_open(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: fd_open pathname\n");
    return;
  }

  int fd = open(cmd->argv[1], O_RDONLY);
  if (fd < 0) {
    perror("open");
    return;
  }

  printf("opened fd %d\n", fd);
}

static void
cmd_fd_openat(struct cmd *cmd) {
  if (cmd->argc != 3) {
    fprintf(stderr, "usage: fd_openat dir_fd pathname\n");
    return;
  }

  int dir_fd = atoi(cmd->argv[1]);
  int fd = openat(dir_fd, cmd->argv[2], O_RDONLY);
  if (fd < 0) {
    perror("openat");
    return;
  }

  printf("opened fd %d\n", fd);
}

static void
cmd_fd_close(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: fd_close fd\n");
    return;
  }

  int fd = atoi(cmd->argv[1]);
  int r = close(fd);
  if (r < 0) {
    perror("close");
  }
}

static void
cmd_fd_read(struct cmd *cmd) {
  if (cmd->argc != 2) {
    fprintf(stderr, "usage: fd_read fd\n");
    return;
  }

  int fd = atoi(cmd->argv[1]);
  for (;;) {
    char buf[1024];
    int cc = read(fd, buf, sizeof(buf));
    if (cc == 0) {
      break;
    }
    if (cc < 0) {
      perror("read");
      return;
    }
    write(1, buf, cc);
  }
}


static const struct cmdimpl cmds[] = {
  { "echo", cmd_echo },
  { "pwd", cmd_pwd },
  { "cd", cmd_cd },
  { "ls", cmd_ls },
  { "cat", cmd_cat },
  { "mkdir", cmd_mkdir },
  { "rmdir", cmd_rmdir },
  { "rm", cmd_rm },
  { "touch", cmd_touch },
  { "mv", cmd_mv },
  { "cp", cmd_cp },
#ifndef DISABLE_LN
  { "ln", cmd_ln },
#endif

  { "fd_list", cmd_fd_list },
  { "fd_open", cmd_fd_open },
  { "fd_openat", cmd_fd_openat },
  { "fd_close", cmd_fd_close },
  { "fd_read", cmd_fd_read },
};

static void panic(char*);
static struct cmd *parsecmd(char*);

// Execute cmd.
static void
runcmd(struct cmd *cmd)
{
  if (cmd->argc == 0)
    return;

  for (int i = 0; i < sizeof(cmds) / sizeof(cmds[0]); i++) {
    if (!strcmp(cmd->argv[0], cmds[i].name)) {
      cmds[i].run(cmd);
      return;
    }
  }

  fprintf(stderr, "unknown command %s; available commands are:\n", cmd->argv[0]);
  fprintf(stderr, " ");
  for (int i = 0; i < sizeof(cmds) / sizeof(cmds[0]); i++) {
    fprintf(stderr, " %s", cmds[i].name);
  }
  fprintf(stderr, "\n");
}

static int
getcmd(char *buf, int nbuf)
{
  write(2, "$ ", 2);
  memset(buf, 0, nbuf);
  fgets(buf, nbuf, stdin);
  if(buf[0] == 0) // EOF
    return -1;
  return 0;
}

int
main(void)
{
  static char buf[128];

  // Read and run input commands.
  while(getcmd(buf, sizeof(buf)) >= 0){
    struct cmd *c = parsecmd(buf);
    if (c) {
      runcmd(c);
    } else {
      fprintf(stderr, "cannot parse\n");
    }
    fflush(stdout);
    fflush(stderr);
  }
  exit(0);
}

static void
panic(char *s)
{
  fprintf(stderr, "%s\n", s);
  exit(1);
}

// Parsing

char whitespace[] = " \t\r\n\v";

static int
gettoken(char **ps, char *es, char **q, char **eq)
{
  char *s;
  int ret;

  s = *ps;
  while(s < es && strchr(whitespace, *s))
    s++;
  if(q)
    *q = s;
  ret = *s;
  switch(*s){
  case 0:
    break;
  default:
    ret = 'a';
    while(s < es && !strchr(whitespace, *s))
      s++;
    break;
  }
  if(eq)
    *eq = s;

  while(s < es && strchr(whitespace, *s))
    s++;
  *ps = s;
  return ret;
}

static int
peek(char **ps, char *es, char *toks)
{
  char *s;

  s = *ps;
  while(s < es && strchr(whitespace, *s))
    s++;
  *ps = s;
  return *s && strchr(toks, *s);
}

static struct cmd*
parseexec(char **ps, char *es)
{
  char *q, *eq;
  int tok, argc;
  struct cmd *cmd;

  cmd = malloc(sizeof(*cmd));

  argc = 0;
  while(!peek(ps, es, "")){
    if((tok=gettoken(ps, es, &q, &eq)) == 0)
      break;
    if(tok != 'a')
      panic("syntax");
    cmd->argv[argc] = q;
    cmd->eargv[argc] = eq;
    argc++;
    if(argc >= MAXARGS)
      panic("too many args");
  }
  cmd->argc = argc;
  return cmd;
}

// NUL-terminate all the counted strings.
static struct cmd*
nulterminate(struct cmd *cmd)
{
  int i;
  for(i=0; i<cmd->argc; i++)
    *cmd->eargv[i] = 0;
  return cmd;
}

static struct cmd*
parsecmd(char *s)
{
  char *es;
  struct cmd *cmd;

  es = s + strlen(s);
  cmd = parseexec(&s, es);
  peek(&s, es, "");
  if(s != es){
    fprintf(stderr, "leftovers: %s\n", s);
    return 0;
  }
  nulterminate(cmd);
  return cmd;
}
