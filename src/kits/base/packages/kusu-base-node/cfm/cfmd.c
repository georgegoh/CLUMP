/*
   Copyright (C) 2007 Platform Computing Inc

   This program is free software; you can redistribute it and/or modify
   it under the terms of version 2 of the GNU General Public License as
   published by the Free Software Foundation.
 	
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

*/

/* This is the maximun time that the CFM client process can
   run (in seconds). */
#define MAXRUNTIME 3600



#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <errno.h>
#include <assert.h>
#include <stdarg.h>
#include <time.h>
#include <signal.h>
#include <fcntl.h>
#include <setjmp.h>
#include <math.h>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

/* For the networking code */
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

#define UNIX 1

#ifdef UNIX
#define CFM_SEQUENCE  "/opt/kusu/etc/.sequence.client"
#define CFM_NODEGROUP "/etc/profile.nii"
#endif

/*
 * Severities of log messages
 */
typedef enum {
    LOG_FATAL,                /* Irrecoverable error */
    LOG_ERROR,                /* Severe, but recoverable error */
    LOG_WARNING,              /* Insignificant error */
    LOG_INFO,                 /* Information of some interest to user */
    LOG_DEBUG                 /* Information of no interest to user */
} LOG_LEVEL;

/* The loggingLevel controls the default log level */
static int loggingLevel = LOG_FATAL ;


/* The packet structure is built from a series of strings
   A binary structure did not seem possible with python?!? */
struct rawPacketInstance {
  char magic[8] ;
  char sequence[8] ;
  char version[8] ;
  char type[8] ;
  char ngid[8] ;
  char waittime[8] ;
  char installers[10][8] ;
} ;

/* The processed packet structure */
struct dataPack {
  int sequence ;
  int version ;
  int type ;
  int ngid ;
  int waittime ;
  char installers[10][16] ;
} ;

static void randSleep(int maxsleep) ;
static void daemonize() ;
static int getSequence() ;
static int setSequence(int seq) ;
static int getNGID() ;
static int setInstallers(struct dataPack *dpack) ;
static int getInstallers(struct dataPack *dpack) ;
static int cfmLog(LOG_LEVEL level, const char* format, ...) ;
static int runUpdate(struct dataPack *dpack) ;


int main(int argc, char* argv[])
{
  int ngid = 0 ;
  int sequence = 0 ;
  int sd = 0 ;
  int i ;
  int sent = 0 ;
  int mkdaemon = 1 ;
  struct dataPack dpack ;
  struct dataPack testpack ;
 
  while (--argc) {
    ++argv;
      switch ((*argv)[1]) {
      case 'v':
	/* Verbosity */
	if(argc) {
          ++argv ;
          loggingLevel = atoi(*argv) ;
	  if(loggingLevel < 0 || loggingLevel > 4)
	    loggingLevel = LOG_FATAL ;
        }
	--argc ;
        break ;
      case 'd':
	/* Don't Daemonize */
	mkdaemon = 0 ;
	break ;
      case 'h':
	/* Basic Help */
	printf("Usage:  cfmd {optional argumnets}\n") ;
	printf("The Cluster File Management Daemon (CFMD) listens for CFM\n") ;
	printf("updates and triggers file and or package updates. \n") ;
	printf("The optional arguments are only for debugging!\n") ;
	printf(" -h        - This help info.\n") ;
	printf(" -d        - Don't daemonize\n") ;
	printf(" -v [0-4]  - Logging verbosity\n") ;
	exit(0) ;
	break ;
      }
      
  }
  cfmLog(LOG_INFO, "Starting cfmd.  Debug level = %i\n", loggingLevel) ;

  sequence = getSequence() ;
  cfmLog(LOG_DEBUG, "Starting Local Sequence Number = %i\n", sequence) ;

  ngid = getNGID() ;
  cfmLog(LOG_DEBUG, "NGID = %i\n", ngid) ;

  if(mkdaemon) 
    daemonize() ;

  sd = setupSocket() ;

  while(1)
    {
      listen4packet(sd, &dpack) ;

      if(dpack.sequence <= sequence)
	{
	  if(!sent)
	    {
	      sent = 1 ;
	      cfmLog(LOG_DEBUG, "Ignoring duplicate packet(s)\n") ;
	    }
	  continue ;
	}
      sent = 0 ;

      if(dpack.ngid != 0 && dpack.ngid != ngid)
	{
	  cfmLog(LOG_DEBUG, "Ignoring update for ngid = %i\n", dpack.ngid) ;
	  continue ;
	}
      
      /* Store all tje information we will need later */
      sequence = dpack.sequence ;
      setSequence(dpack.sequence) ;
      setInstallers(&dpack) ;

      cfmLog(LOG_DEBUG, "Sequence number = %i\n", dpack.sequence) ;
      cfmLog(LOG_DEBUG, "Local Sequence = %i\n", sequence) ;
      cfmLog(LOG_DEBUG, "Version number = %i\n", dpack.version) ;
      cfmLog(LOG_DEBUG, "Update type = %i\n", dpack.type) ;
      cfmLog(LOG_DEBUG, "NGID number = %i\n", dpack.ngid) ;
      cfmLog(LOG_DEBUG, "Waittime = %i\n", dpack.waittime) ;
      for(i=0; i<10; i++)
	{
	  if(dpack.installers[i][0] == 0)
	    break ;
	  
	  cfmLog(LOG_DEBUG, "Installer[%i] = %s\n", i, dpack.installers[i]) ;
	}
  
      randSleep(dpack.waittime) ;

      runUpdate(&dpack) ;
    }

}

/* randSleep - Sleep for a random number of seconds */
static void randSleep(int maxsleep)
{
  int sleepfor = 0 ;
  float f = 0.0 ;

  if(maxsleep)
    {
      f = (float)rand() / RAND_MAX * maxsleep ;
      sleepfor = (int)ceilf(f) ;
      cfmLog(LOG_DEBUG, "Sleeping for %i seconds\n", sleepfor) ;
      if(sleepfor)
	sleep(sleepfor) ;
    }
}

static void daemonize()
{
  int pid = fork();

  if (pid < 0) 
    {
      fprintf(stderr, "Cannot fork: %s\n", strerror(errno)) ;
      return ;
    }
  if (pid > 0) 
    exit(0) ;
  setsid() ;
  close(2) ;
}


/* getSequence - Get the current sequence number from file */
static int getSequence()
{
  FILE* fd = NULL ;
  char buff[16] ;

  if ((fd = fopen(CFM_SEQUENCE, "r")) == NULL ) 
    return(0) ;

  fgets(buff, sizeof(buff), fd) ;
  fclose(fd) ;
  
  if(buff[0])
      return(atoi(buff)) ;

  return(0) ;
}


/* setSequence - Write the current sequence number to file */
static int setSequence(int seq)
{
  FILE* fd = NULL ;
  char buff[512] ;

  memset(buff, 0, 512) ;
  if ((fd = fopen(CFM_SEQUENCE, "r")) == NULL ) 
    return(0) ;

  fgets(buff, sizeof(buff), fd) ;  /* Read in the sequence number */
  fread(buff, 1, 512, fd) ;
  fclose(fd) ;

  if ((fd = fopen(CFM_SEQUENCE, "w")) == NULL ) 
    return(0) ;

  buff[511] = 0 ;
  fprintf(fd, "%i\n", seq) ;
  fwrite(buff, 1, strlen(buff+1), fd) ;
  fclose(fd) ;

  return(seq) ;
}


/* getInstallers - Get the list of available installers from 
   the CFM_SEQUENCE file.   */
static int getInstallers(struct dataPack *dpack)
{
  FILE* fd = NULL ;
  char buff[20] ;
  int i ;

  if ((fd = fopen(CFM_SEQUENCE, "r")) == NULL ) 
    return(0) ;

  fgets(buff, sizeof(buff), fd) ;  /* This is the sequence */
  for(i=0; i<10; i++)
    {
      if(fgets(buff, sizeof(buff), fd) == NULL) /* This is the installers */
	{
	  /* No more installers */
	  memset(&dpack->installers[i][0], 0, 16) ;
	  break ;
	}
      strncpy(dpack->installers[i], buff, 15) ;
    }
  fclose(fd) ;

  return(0) ;
}


/* setInstallers - Write the current installer list to file */
static int setInstallers(struct dataPack *dpack)
{
  FILE* fd = NULL ;
  char buff[16] ;
  int sequence = 0 ;
  int i ;

  sequence = getSequence() ;

  if ((fd = fopen(CFM_SEQUENCE, "w")) == NULL ) 
    return(-1) ;

  fprintf(fd, "%i\n", sequence) ;
  for(i=0; i<10; i++)
    {
      if(dpack->installers[i][0] == 0)
	break ;
      fprintf(fd, "%s\n", dpack->installers[i]) ;
    }
  fclose(fd) ;

  return(i) ;
}


/* getNGID - Get the node group ID number from file. 
             This function will have to change. */
static int getNGID()
{
  FILE* fd = NULL ;
  char buff[256] ;
  int retval = 0 ;

  if ((fd = fopen(CFM_NODEGROUP, "r")) == NULL ) 
    return(0) ;

  while (fgets(buff, sizeof(buff), fd) != NULL)
    {
      if ( ! strncmp(buff, "export NII_NGID=", strlen("export NII_NGID=")) )
	{
	  retval = atoi(&buff[strlen("export NII_NGID=")]) ;
	}
    }
  fclose(fd) ;
  
  return(retval) ;
}


/* setupSocket - Create a socket for listening for broadcasts.
 */
int setupSocket()
{
  int sd ;
  const int on = 1 ;
  struct protoent    *proto ;
  struct servent     *sport ;
  struct hostent     *host;
  struct sockaddr_in sin;

  memset(&sin, 0, sizeof(sin));

  sin.sin_family = AF_INET;
  sin.sin_port = htons(65001) ;

  if ((proto = (struct protoent *)getprotobyname("udp")) == NULL) {
    return (-1);
  }

  cfmLog(LOG_DEBUG, "Proto number = %i\n", proto->p_proto) ;

  if((sd = socket(PF_INET, SOCK_DGRAM, proto->p_proto)) == -1) {
    cfmLog(LOG_FATAL, "ERROR:  Socket failed\n") ;
    return(-1) ;
  }

  memset(&sin, 0, sizeof(sin));

  sin.sin_family = AF_INET;
  sin.sin_addr.s_addr = htonl(INADDR_ANY) ;
  if ((sport = (struct servent *)getservbyname("cfm", "udp")) == NULL) 
    {
      sin.sin_port = htons(65001) ;
    } 
  else 
    {
      sin.sin_port = sport->s_port ;
    }
  cfmLog(LOG_DEBUG, "Port number = %i\n", ntohs(sin.sin_port)) ;

  /* Allow address reuse */
  setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on)) ;

  /* Set the broadcast options */
  setsockopt(sd, SOL_SOCKET, SO_BROADCAST, &on, sizeof(on)) ;

  bind(sd, (const struct sockaddr *)&sin, sizeof(sin)) ;

  return(sd) ;
}


int listen4packet(int sd, struct dataPack *dpack)
{
  char rbuff[512] ;
  char convert[16] ;
  ssize_t read ;
  int i = 0 ;
  int j = 0 ;
  int intval = 0 ;
  struct rawPacketInstance *pack = NULL ;

  memset(rbuff, 0, sizeof(rbuff)) ;

  read = recvfrom(sd, rbuff, sizeof(rbuff), 0, NULL, NULL) ;
  rbuff[read] = 0 ;

  if(strncmp(rbuff, "MaRkScFm", strlen("MaRkScFm")))
    {
      /* Not a CFM packet */
      return(-1) ;
    }

  pack = (struct rawPacketInstance *)rbuff ;
  
  /* Sequence Number */
  intval = 0 ;
  convert[0] = convert[1] = 0 ;
  for(i=0; i<8; i++)
    {
      intval = intval << 4 ;
      if(pack->sequence[i])
	{
	  convert[0] = pack->sequence[i] ;
	  intval = intval + strtol(convert, NULL, 16) ;
	}
    }
  dpack->sequence = intval ;

  /* Version Number */
  intval = 0 ;
  convert[0] = convert[1] = 0 ;
  for(i=0; i<8; i++)
    {
      intval = intval << 4 ;
      if(pack->version[i])
	{
	  convert[0] = pack->version[i] ;
	  intval = intval + strtol(convert, NULL, 16) ;
	}
    }
  dpack->version = intval ;

  /* Update Type */
  intval = 0 ;
  convert[0] = convert[1] = 0 ;
  for(i=0; i<8; i++)
    {
      intval = intval << 4 ;
      if(pack->type[i])
	{
	  convert[0] = pack->type[i] ;
	  intval = intval + strtol(convert, NULL, 16) ;
	}
    }
  dpack->type = intval ;

  /* NGID Number */
  intval = 0 ;
  convert[0] = convert[1] = 0 ;
  for(i=0; i<8; i++)
    {
      intval = intval << 4 ;
      if(pack->ngid[i])
	{
	  convert[0] = pack->ngid[i] ;
	  intval = intval + strtol(convert, NULL, 16) ;
	}
    }
  dpack->ngid = intval ;
  
  /* Waittime */
  intval = 0 ;
  convert[0] = convert[1] = 0 ;
  for(i=0; i<8; i++)
    {
      intval = intval << 4 ;
      if(pack->waittime[i])
	{
	  convert[0] = pack->waittime[i] ;
	  intval = intval + strtol(convert, NULL, 16) ;
	}
    }
  dpack->waittime = intval ;

  /* Installer List */
  for(i=0; i<10; i++)
    {
      memset(&dpack->installers[i][0], 0, 16) ;
      memset(convert, 0, 16) ;
      if(pack->installers[i][0] == '0' && pack->installers[i][1] == '0')
	break ;

      for(j=0; j<8; j++) 
	{
	  convert[2*j] = pack->installers[i][j] ;
	}
      sprintf(dpack->installers[i], "%i.%i.%i.%i", \
	      (strtol(&convert[0], NULL, 16) << 4 ) + \
	      strtol(&convert[2], NULL, 16), \
	      (strtol(&convert[4], NULL, 16) << 4 ) + \
	      strtol(&convert[6], NULL, 16), \
	      (strtol(&convert[8], NULL, 16) << 4 ) + \
	      strtol(&convert[10], NULL, 16), \
	      (strtol(&convert[12], NULL, 16) << 4 ) + \
	      strtol(&convert[14], NULL, 16)) ;
    }

  /* For Debugging
  for(i=0; i<16; i++)
    {
      printf("Char[%i] = ", (int)i) ;
      for(j=0; j<8; j++)
	{
	  if(isalnum(rbuff[(i* 8) + j]))
	    {
	      printf("%c", rbuff[(i* 8) + j]) ;
	    }
	  else
	    {
	      printf(".") ;
	    }
	}
      printf("\n") ;
      } */

  return(0) ;
}


/* log - log messages.  Note messages should not exceed 1K */
static int cfmLog(LOG_LEVEL level, const char* format, ...)
{
  char *msgBuf  = NULL;
  va_list vl;
  static int lflag = 1 ;

  if(level <= loggingLevel)
    {
      msgBuf = (char *) calloc(1024, sizeof(char));
      if(msgBuf == NULL) 
	{
	  if(lflag)
	    {
	      fprintf(stderr, "FATAL:  Logging not available!\n") ;
	      lflag = 0 ;
	    }
	}
      va_start(vl, format);
      vsprintf(msgBuf, format, vl);
      va_end(vl);
      
      printf("%s", msgBuf) ;
      free(msgBuf) ;
    }
  return(0) ;
}

  
/* runUpdate - Run the CFM update client and wait for it
   to finish */
static int runUpdate(struct dataPack *dpack)
{
  pid_t pid ;
  int options ;
  int status = 0 ;
  int waited = 0 ;
  pid_t retval ;

  pid = fork() ;

  if(pid)
    cfmLog(LOG_DEBUG, "Started update process.  pid=%i\n", pid) ;

  if(pid == 0)
    {
      /* This is the child */
      char utype[16] ;
      char ilist[256] ;
      int i ;
      
      /* Build the list of installers (comma seperated) */
      memset(ilist, 0, sizeof(ilist)) ;
      memset(utype, 0, sizeof(utype)) ;
      for(i=0; i<10; i++)
	{
	  if(dpack->installers[i][0] == 0)
	    break ;
	  
	  strncat(ilist, dpack->installers[i], strlen("123.456.789.123")) ;
	  strcat(ilist, ",") ;
	}

      if(strlen(ilist) > 3)
	ilist[strlen(ilist) -1 ] = 0 ;
       
      snprintf(utype, 14, "%i", dpack->type) ;

      cfmLog(LOG_DEBUG, "Running: /opt/kusu/sbin/cfmclient -t %s -i %s\n", utype, ilist) ;

      close(STDIN_FILENO) ;
      close(STDOUT_FILENO) ;
      close(STDERR_FILENO) ;

      execl("/opt/kusu/sbin/cfmclient", "cfmclient", "-t", utype, "-i", ilist, (char *)0) ;

      exit(-1) ;
    }
  else if(pid == -1)
    {
      cfmLog(LOG_ERROR, "Unable to start CFM update client!\n") ;
    }
 
  /* This is the parent.  Monitor the child process and allow it
     to run for a time, then kill it if it has not finished */
  while(1)
    {
      sleep(1) ;            /* don't chew-up CPU */
      waited++ ;
      options = WNOHANG ;
      retval = waitpid(pid, &status, options) ;

      /* Kill the child process if it has been taking too long */
      if(waited >= MAXRUNTIME)
	{
	  cfmLog(LOG_WARNING, "Update process is taking too long.  Stopping it!  pid=%i\n", pid) ;
	  kill(pid, SIGTERM) ;
	  sleep(1) ;
	  options = WNOHANG ;
	  retval = waitpid(pid, &status, options) ;
	  if(retval == 0)
	    {
	      kill(pid, SIGKILL) ;
	      cfmLog(LOG_WARNING, "Sending kill signal to pid: %i\n", pid) ;
	    }
	}

      if(retval == 0)
	continue ;

      /* Child is dead */
      if(WIFEXITED(status))
	{
	  cfmLog(LOG_DEBUG, "Child process exited normally with: %i\n", WEXITSTATUS(status)) ;
	}
      else
	{
	  cfmLog(LOG_WARNING, "Child process terminated abnormally!\n") ;
	}

      break ;
    }
}
