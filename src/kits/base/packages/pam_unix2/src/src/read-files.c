/* Copyright (C) 2002, 2003 Thorsten Kukuk
   Author: Thorsten Kukuk <kukuk@suse.de>

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License version 2 as
   published by the Free Software Foundation.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  */


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <pwd.h>
#include <shadow.h>
#include <ctype.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <nss.h>
#include <bits/libc-lock.h>
#define __libc_lock_t pthread_mutex_t

#include "read-files.h"

static enum { none, getent, getby }last_use;

#define ISCOLON(c) ((c) == ':')

#define STRING_FIELD(variable, terminator_p, swallow)                        \
  {                                                                           \
    variable = line;                                                          \
    while (*line != '\0' && !terminator_p (*line))                            \
      ++line;                                                                 \
    if (*line != '\0')                                                        \
      {                                                                       \
        *line = '\0';                                                         \
        do                                                                    \
          ++line;                                                             \
        while (swallow && terminator_p (*line));                              \
      }                                                                       \
  }

#define INT_FIELD(variable, terminator_p, swallow, base, convert)            \
  {                                                                           \
    char *endp;                                                               \
    variable = convert (strtoul (line, &endp, base));                         \
    if (endp == line)                                                         \
      return 0;                                                               \
    else if (terminator_p (*endp))                                            \
      do                                                                      \
        ++endp;                                                               \
      while (swallow && terminator_p (*endp));                                \
    else if (*endp != '\0')                                                   \
      return 0;                                                               \
    line = endp;                                                              \
  }

#define INT_FIELD_MAYBE_NULL(variable, terminator_p, swallow, base, convert, default)        \
  {                                                                           \
    char *endp;                                                               \
    if (*line == '\0')                                                        \
      /* We expect some more input, so don't allow the string to end here. */ \
      return 0;                                                               \
    variable = convert (strtoul (line, &endp, base));                         \
    if (endp == line)                                                         \
      variable = default;                                                     \
    if (terminator_p (*endp))                                                 \
      do                                                                      \
        ++endp;                                                               \
      while (swallow && terminator_p (*endp));                                \
    else if (*endp != '\0')                                                   \
      return 0;                                                               \
    line = endp;                                                              \
  }

static inline int
parse_pwent (char *line, struct passwd *result)
{
  char *p = strpbrk (line, "\n");
  if (p != NULL)
    *p = '\0';
  STRING_FIELD (result->pw_name, ISCOLON, 0);
  if (line[0] == '\0'
      && (result->pw_name[0] == '+' || result->pw_name[0] == '-'))
    {
      /* This a special case.  We allow lines containing only a `+' sign
        since this is used for nss_compat.  All other services will
        reject this entry later.  Initialize all other fields now.  */
     result->pw_passwd = NULL;
     result->pw_uid = 0;
     result->pw_gid = 0;
     result->pw_gecos = NULL;
     result->pw_dir = NULL;
     result->pw_shell = NULL;
   }
 else
   {
     STRING_FIELD (result->pw_passwd, ISCOLON, 0);
     if (result->pw_name[0] == '+' || result->pw_name[0] == '-')
       {
         INT_FIELD_MAYBE_NULL (result->pw_uid, ISCOLON, 0, 10, , 0)
         INT_FIELD_MAYBE_NULL (result->pw_gid, ISCOLON, 0, 10, , 0)
       }
     else
       {
         INT_FIELD (result->pw_uid, ISCOLON, 0, 10,)
         INT_FIELD (result->pw_gid, ISCOLON, 0, 10,)
       }
     STRING_FIELD (result->pw_gecos, ISCOLON, 0);
     STRING_FIELD (result->pw_dir, ISCOLON, 0);
     result->pw_shell = line;
   }
  return 1;
}


/* Predicate which always returns false, needed below.  */
#undef FALSE
#define FALSE(arg) 0

static inline int
parse_spent (char *line, struct spwd *result)
{
  char *p = strpbrk (line, "\n");
  if (p != NULL)
    *p = '\0';

 result->sp_namp = line;
 while (*line != '\0' && !ISCOLON (*line))
   ++line;
 if (*line != '\0')
   {
     *line = '\0';
     ++line;
   }

 if (line[0] == '\0'
     && (result->sp_namp[0] == '+' || result->sp_namp[0] == '-'))
   {
     result->sp_pwdp = NULL;
     result->sp_lstchg = 0;
     result->sp_min = 0;
     result->sp_max = 0;
     result->sp_warn = -1l;
     result->sp_inact = -1l;
     result->sp_expire = -1l;
     result->sp_flag = ~0ul;
   }
 else
   {
     result->sp_pwdp = line;
     while (*line != '\0' && !ISCOLON (*line))
       ++line;
     if (*line != '\0')
       {
	 *line = '\0';
	 ++line;
       }
     INT_FIELD_MAYBE_NULL (result->sp_lstchg, ISCOLON, 0, 10, (long int),
                           (long int) -1);
     INT_FIELD_MAYBE_NULL (result->sp_min, ISCOLON, 0, 10, (long int),
                           (long int) -1);
     INT_FIELD_MAYBE_NULL (result->sp_max, ISCOLON, 0, 10, (long int),
                           (long int) -1);
     while (isspace (*line))
       ++line;
     if (*line == '\0')
       {
         /* The old form.  */
         result->sp_warn = -1l;
         result->sp_inact = -1l;
         result->sp_expire = -1l;
         result->sp_flag = ~0ul;
       }
     else
       {
         INT_FIELD_MAYBE_NULL (result->sp_warn, ISCOLON, 0, 10, (long int),
                               (long int) -1);
         INT_FIELD_MAYBE_NULL (result->sp_inact, ISCOLON, 0, 10, (long int),
                               (long int) -1);
         INT_FIELD_MAYBE_NULL (result->sp_expire, ISCOLON, 0, 10, (long int),
                               (long int) -1);
         if (*line != '\0')
           INT_FIELD_MAYBE_NULL (result->sp_flag, FALSE, 0, 10,
                                 (unsigned long int), ~0ul)
         else
           result->sp_flag = ~0ul;
       }
   }
  return 1;
}


static enum nss_status
internal_setent (FILE **stream, const char *file)
{
  enum nss_status status = NSS_STATUS_SUCCESS;

  if (*stream == NULL)
    {
      char *filename = alloca (strlen (files_etc_dir) + 8);
      strcpy (filename, files_etc_dir);
      strcat (filename, file);

      *stream = fopen (filename, "r");

      if (*stream == NULL)
	status = errno == EAGAIN ? NSS_STATUS_TRYAGAIN : NSS_STATUS_UNAVAIL;
      else
	{
	  int result, flags;

	  result = flags = fcntl (fileno (*stream), F_GETFD, 0);
	  if (result >= 0)
	    {
	      flags |= 1;
	      result = fcntl (fileno (*stream), F_SETFD, flags);
	    }

	  if (result < 0)
	    {
	      fclose (*stream);
	      stream = NULL;
	      status = NSS_STATUS_UNAVAIL;
	    }
	}
    }
  else
    rewind (*stream);

  return status;
}

static void
internal_endent (FILE **stream)
{
  if (*stream != NULL)
    {
      fclose (*stream);
      stream = NULL;
    }
}

static enum nss_status
internal_getspent (FILE *stream, struct spwd *result,
		   char *buffer, size_t buflen, int *errnop)
{
  char *p;
  char *data = (void *) buffer;
  int linebuflen = buffer + buflen - data;
  int parse_result;

  if (buflen < sizeof *data + 2)
    {
      *errnop = ERANGE;
      return NSS_STATUS_TRYAGAIN;
    }

  do {
    ((unsigned char *) data)[linebuflen - 1] = '\xff';

    p = fgets (data, linebuflen, stream);
    if (p == NULL)
      {
	*errnop = ENOENT;
	return NSS_STATUS_NOTFOUND;
      }
    else if (((unsigned char *) data)[linebuflen - 1] != 0xff)
      {
	*errnop = ERANGE;
	return NSS_STATUS_TRYAGAIN;
      }

    /* Skip leading blanks.  */
    while (isspace (*p))
      ++p;
  }
  while (*p == '\0' || *p == '#'
	 || !(parse_result = parse_spent (p, result)));


  return parse_result == -1 ? NSS_STATUS_TRYAGAIN : NSS_STATUS_SUCCESS;
}

static enum nss_status
internal_getpwent (FILE *stream, struct passwd *result,
		   char *buffer, size_t buflen, int *errnop)
{
  char *p;
  char *data = (void *) buffer;
  int linebuflen = buffer + buflen - data;
  int parse_result;

  if (buflen < sizeof *data + 2)
    {
      *errnop = ERANGE;
      return NSS_STATUS_TRYAGAIN;
    }

  do {
    ((unsigned char *) data)[linebuflen - 1] = '\xff';

    p = fgets (data, linebuflen, stream);
    if (p == NULL)
      {
	*errnop = ENOENT;
	return NSS_STATUS_NOTFOUND;
      }
    else if (((unsigned char *) data)[linebuflen - 1] != 0xff)
      {
	*errnop = ERANGE;
	return NSS_STATUS_TRYAGAIN;
      }

    /* Skip leading blanks.  */
    while (isspace (*p))
      ++p;
  }
  while (*p == '\0' || *p == '#'
	 || !(parse_result = parse_pwent (p, result)));


  return parse_result == -1 ? NSS_STATUS_TRYAGAIN : NSS_STATUS_SUCCESS;
}

enum nss_status
files_getspnam_r (const char *name, struct spwd *result,
		  char *buffer, size_t buflen, int *errnop)
{
  /* Locks the static variables in this file.  */
  __libc_lock_define_initialized (static, lock)
  enum nss_status status;
  FILE *stream = NULL;

  __libc_lock_lock (lock);

  status = internal_setent (&stream, "/shadow");
  if (status == NSS_STATUS_SUCCESS)
    {
      last_use = getby;
      while ((status = internal_getspent (stream, result, buffer, buflen,
					  errnop)) == NSS_STATUS_SUCCESS)
	{
	  if (name[0] != '+' && name[0] != '-'
	      && ! strcmp (name, result->sp_namp))
	    break;
	}
      internal_endent (&stream);
    }

  __libc_lock_unlock (lock);

  return status;
}

enum nss_status
files_getpwnam_r (const char *name, struct passwd *result,
		  char *buffer, size_t buflen, int *errnop)
{
  /* Locks the static variables in this file.  */
  __libc_lock_define_initialized (static, lock)
  enum nss_status status;
  FILE *stream = NULL;

  __libc_lock_lock (lock);

  status = internal_setent (&stream, "/passwd");
  if (status == NSS_STATUS_SUCCESS)
    {
      last_use = getby;
      while ((status = internal_getpwent (stream, result, buffer, buflen,
					  errnop)) == NSS_STATUS_SUCCESS)
	{
	  if (name[0] != '+' && name[0] != '-'
	      && ! strcmp (name, result->pw_name))
	    break;
	}
      internal_endent (&stream);
    }

  __libc_lock_unlock (lock);

  return status;
}
