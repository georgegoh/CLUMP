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
#include <stdarg.h>
#include <time.h>
#include <signal.h>
#include <fcntl.h>
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
#define CFM_SEQUENCE  "/etc/.cfm.client.sequence"
#define CFM_PROFILE_NII "/etc/profile.nii"
#endif

#define CFMCLIENT_BINARY "/opt/kusu/sbin/cfmclient"

#define CFMD_PORT ((unsigned short) 65001)

#define UPDATEFILE 1
#define UPDATEPACKAGE 2
#define FORCEFILES 4            /* Force the files to be updated */


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
static void daemonize(void) ;
static int getSequence(void) ;
static int setSequence(int seq) ;
static int getNGID(void) ;
static int setInstallers(struct dataPack *dpack) ;
static int getInstallers(struct dataPack *dpack) ;
static int getNiiInstallers(struct dataPack *dpack) ;
static int cfmLog(LOG_LEVEL level, const char* format, ...) ;
static void runUpdate(struct dataPack *dpack) ;
static int setupSocket(void);
static int listen4packet(int sd, struct dataPack *dpack);

int main(int argc, char* argv[])
{
  int ngid = 0 ;
  int sequence = 0 ;
  int sd = 0 ;
  int i ;
  int sent = 0 ;
  int mkdaemon = 1 ;
  struct dataPack dpack ;
 
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

  if(!ngid)
    {
      cfmLog(LOG_FATAL, "Unable to determine the NGID. The /etc/profile.nii is damaged\n") ;
      exit(-1) ;
    }

  if(mkdaemon) 
    daemonize() ;

  /* Run the update process on startup */
  if(getInstallers(&dpack))
    {
      dpack.type = UPDATEFILE | UPDATEPACKAGE ;
      cfmLog(LOG_DEBUG, "On startup update type = %i\n", dpack.type) ;
      runUpdate(&dpack) ;
    } 
  else
    {
      /* No installer list available!  Revert to the NII installer */
      if(getNiiInstallers(&dpack))
	{
	  dpack.type = UPDATEFILE | UPDATEPACKAGE | FORCEFILES ;
	  cfmLog(LOG_DEBUG, "Using NII host: %s\n", dpack.installers[0]) ;
	  cfmLog(LOG_DEBUG, "On startup update type = %i\n", dpack.type) ;
	  runUpdate(&dpack) ;
	}
      else
	{
	  cfmLog(LOG_WARNING, "Unable to determine the NII host!  Cannot synchronize now.\n") ;
	}
    }

  sd = setupSocket() ;
  if (sd == -1) {
    cfmLog(LOG_ERROR, "Error setting up socket (%m)\n") ;
    exit(1);
  }

  while(1)
    {
      if (listen4packet(sd, &dpack) == -1) {
        /* Received non-CFM packet */
        continue;
      }

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

    return(0) ;
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

static void daemonize(void)
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
static int getSequence(void)
{
  FILE* fd = NULL ;
  char buff[16] ;

  memset(buff, 0, sizeof(buff)) ;
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
  static char buff[512] ;

  if ((fd = fopen(CFM_SEQUENCE, "r")) == NULL ) 
    return(0) ;

  fgets(buff, sizeof(buff), fd) ;  /* Read in the sequence number */
  memset(buff, 0, sizeof(buff)) ;
  fread(buff, 1, sizeof(buff)-2, fd) ;
  fclose(fd) ;

  if ((fd = fopen(CFM_SEQUENCE, "w")) == NULL ) 
    return(0) ;

  fprintf(fd, "%i\n", seq) ;
  fwrite(buff, 1, strlen(buff), fd) ;
  fclose(fd) ;

  return(seq) ;
}


/* getInstallers - Get the list of available installers from 
   the CFM_SEQUENCE file.   */
static int getInstallers(struct dataPack *dpack)
{
  FILE* fd = NULL ;
  char *dptr = NULL ;
  char buff[20] ;
  int i ;

  memset(&dpack->installers[0][0], 0, 16) ;
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
      if((dptr = strstr(buff, "\n")) != NULL )
	*dptr = 0 ;

      strncpy(dpack->installers[i], buff, 15) ;
    }
  fclose(fd) ;

  return(i) ;
}


/* setInstallers - Write the current installer list to file */
static int setInstallers(struct dataPack *dpack)
{
  FILE* fd = NULL ;
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
static int getNGID(void)
{
  FILE* fd = NULL ;
  static char buff[256] ;
  int retval = 0 ;

  if ((fd = fopen(CFM_PROFILE_NII, "r")) == NULL ) 
    return(0) ;

  while (fgets(buff, sizeof(buff), fd) != NULL)
    {
      if ( ! strncmp(buff, "export NII_NGID=", strlen("export NII_NGID=")) )
	{
	  retval = atoi(&buff[strlen("export NII_NGID=")]) ;
          break;
	}
    }
  fclose(fd) ;
  
  return(retval) ;
}


/* getNiiInstallers - Get the name of the Installer(s) from the profile.nii
             This function will have to change if the nodeboot.cgi.py changes.
	     NOTE:  An IP address is expected!
*/
static int getNiiInstallers(struct dataPack *dpack)
{
  FILE* fd = NULL ;
  static char buff[256] ;
  char *startptr = NULL ;
  char *endptr   = NULL ;
  int i ;

  for(i=0; i<10; i++)
    memset(&dpack->installers[i][0], 0, 16) ;

  if ((fd = fopen(CFM_PROFILE_NII, "r")) == NULL ) 
    return(0) ;

  while (fgets(buff, sizeof(buff), fd) != NULL)
    {
      if ( ! strncmp(buff, "export NII_INSTALLERS=", strlen("export NII_INSTALLERS=")) )
	{
	  startptr = &buff[strlen("export NII_INSTALLERS=") + 1 ] ;
	  if ((endptr = strstr(startptr, "\"")) == NULL)
	    {
	      return(0) ;
	    }
	  *endptr = 0 ;
	  strncpy(dpack->installers[0], startptr, 15) ;
	}
    }
  fclose(fd) ;
  
  return(1) ;
}


/* setupSocket - Create a socket for listening for broadcasts.
 */
static int setupSocket()
{
  int sd = -1;
  const int on = 1 ;
  struct protoent    *proto ;
  struct servent     *sport ;
  struct sockaddr_in sin;

  memset(&sin, 0, sizeof(sin));

  sin.sin_family = AF_INET;
  sin.sin_port = htons(CFMD_PORT) ;
  sin.sin_addr.s_addr = htonl(INADDR_ANY) ;

  if ((proto = (struct protoent *)getprotobyname("udp")) == NULL) {
    return (-1);
  }

  cfmLog(LOG_DEBUG, "Proto number = %i\n", proto->p_proto) ;

  if((sd = socket(PF_INET, SOCK_DGRAM, proto->p_proto)) == -1) {
    cfmLog(LOG_FATAL, "ERROR:  Socket failed\n") ;
    return(-1) ;
  }

  if ((sport = (struct servent *)getservbyname("cfm", "udp")) != NULL) 
    {
      /* Use port defined in services, instead of default */
      sin.sin_port = sport->s_port ;
    }
  cfmLog(LOG_DEBUG, "Port number = %u\n", ntohs(sin.sin_port)) ;

  /* Allow address reuse */
  if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on)) != 0) {
    return(-1) ;
  }

  /* Set the broadcast options */
  if (setsockopt(sd, SOL_SOCKET, SO_BROADCAST, &on, sizeof(on)) != 0) {
    return(-1) ;
  }

  if (bind(sd, (const struct sockaddr *)&sin, sizeof(sin)) != 0) {
    return(-1) ;
  }

  return(sd) ;
}


static int listen4packet(int sd, struct dataPack *dpack)
{
  static char rbuff[512] ;
  char convert[16] ;
  ssize_t read ;
  int i = 0 ;
  int j = 0 ;
  int intval = 0 ;
  struct rawPacketInstance *pack = NULL ;

  memset(rbuff, 0, sizeof(rbuff)) ;

  read = recvfrom(sd, rbuff, sizeof(rbuff), 0, NULL, NULL) ;
  if(read <= 0)
    return(0) ;

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
      sprintf(dpack->installers[i], "%ld.%ld.%ld.%ld", \
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


/* log - log messages */
static int cfmLog(LOG_LEVEL level, const char* format, ...)
{
  static char msgBuf[1024];
  va_list vl;

  if(level <= loggingLevel)
    {
      va_start(vl, format);
      vsprintf(msgBuf, format, vl);
      va_end(vl);

      printf("%s", msgBuf) ;
    }
  return(0) ;
}

  
/* runUpdate - Run the CFM update client and wait for it
   to finish */
static void runUpdate(struct dataPack *dpack)
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
      static char ilist[256] ;
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
      else
	{
	  cfmLog(LOG_ERROR, "No Installers specified!  Aborting\n") ;
	  exit(-2) ;
	}

      snprintf(utype, 14, "%i", dpack->type) ;

      /* Set the PYTHONPATH */
      if (setenv("PYTHONPATH", "/opt/kusu/lib/python", 1))
	cfmLog(LOG_ERROR, "Unable to set PYTHONPATH") ;

      cfmLog(LOG_DEBUG, "Running: %s -t %s -i %s\n", CFMCLIENT_BINARY, utype, ilist) ;

      close(STDIN_FILENO) ;
      close(STDOUT_FILENO) ;
      close(STDERR_FILENO) ;

      execl(CFMCLIENT_BINARY, "cfmclient", "-t", utype, "-i", ilist, (char *)0) ;

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
