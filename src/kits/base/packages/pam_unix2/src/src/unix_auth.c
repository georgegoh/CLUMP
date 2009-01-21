/*
 * Copyright (c) 1999-2006 SuSE GmbH Nuernberg, Germany.
 * Author: Thorsten Kukuk <kukuk@suse.de>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, and the entire permission notice in its entirety,
 *    including the disclaimer of warranties.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote
 *    products derived from this software without specific prior
 *    written permission.
 *
 * ALTERNATIVELY, this product may be distributed under the terms of
 * the GNU Public License, in which case the provisions of the GPL are
 * required INSTEAD OF the above restrictions.  (This clause is
 * necessary due to a potential bad interaction between the GPL and
 * the restrictions contained in a BSD-style copyright.)
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#if defined(HAVE_CONFIG_H)
#include <config.h>
#endif

#include <grp.h>
#include <pwd.h>
#include <time.h>
#include <ctype.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <shadow.h>
#include <syslog.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <rpc/rpc.h>
#include <rpc/key_prot.h>

#define PAM_SM_AUTH
#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#if defined(HAVE_XCRYPT_H)
#include <xcrypt.h>
#elif defined(HAVE_CRYPT_H)
#include <crypt.h>
#endif

#include "public.h"


/* This module actually performs UNIX/shadow authentication.  */

/* Try to get username if already entered and known to PAM.  */
static int
need_username (pam_handle_t *pamh, const char **name)
{
  const void *void_name;
  int retval;

  retval = pam_get_item(pamh, PAM_USER, &void_name);
  if (retval != PAM_SUCCESS || void_name == NULL)
    return 1;
  else
    {
      *name = void_name;
      return 0;
    }
}

/* Check if we know already the password.  */
static int
need_password (pam_handle_t *pamh, const char **password,
	       options_t *options)
{
  const void *void_pass;
  int retval;

  retval = pam_get_item (pamh, PAM_AUTHTOK, &void_pass);
  if (retval != PAM_SUCCESS)
    {
      if (options->debug)
	pam_syslog (pamh, LOG_DEBUG, "pam_get_item (PAM_AUTHTOK) failed, return %d",
		   retval);
      return 1;
    }
  else if (void_pass == NULL)
    {
      if (options->use_first_pass)
	{
	  if (options->debug)
	    pam_syslog (pamh, LOG_DEBUG,
			"Cannot get stacked password, don't ask for it");
	  return 0;
	}
      return 1;
    }

  *password = void_pass;
  return 0;
}


int
pam_sm_authenticate (pam_handle_t *pamh, int flags, int argc,
		     const char **argv)
{
  struct crypt_data output;
  int retval;
  int sp_buflen = 256;
  char *sp_buffer = alloca (sp_buflen);
  struct spwd sp_resultbuf;
  struct spwd *sp = NULL;
  int pw_buflen = 256;
  char *pw_buffer = alloca (pw_buflen);
  struct passwd pw_resultbuf;
  struct passwd *pw;
  const char *name = NULL;
  const char *password = NULL;
  const char *service;
  const char *salt;
  options_t options;
  int ask_user, ask_password;

  memset (&output, 0, sizeof (output));
  memset (&options, 0, sizeof (options));

  if (get_options (pamh, &options, "auth", argc, argv) < 0)
    {
      pam_syslog (pamh, LOG_ERR, "cannot get options");
      return PAM_SYSTEM_ERR;
    }

  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "pam_sm_authenticate() called");

  ask_user = need_username (pamh, &name);
  ask_password = need_password (pamh, &password, &options);

  if (ask_user)
    {
      retval = __get_tokens (pamh, ask_user, ask_password,
			     &name, &password);
      if (retval != PAM_SUCCESS)
	{
	  if (options.debug)
	    pam_syslog (pamh, LOG_DEBUG, "__get_tokens failed with %d, exit",
			retval);
	  return retval;
	}
    }

  if (name == NULL || name[0] == '\0')
    {
      if (name)
	{
	  if (options.debug)
	    pam_syslog (pamh, LOG_DEBUG, "bad username [%s]", name);
	  return PAM_USER_UNKNOWN;
	}
      else if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "name == NULL, return PAM_SERVICE_ERR");
      return PAM_SERVICE_ERR;
    }
  else if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "username=[%s]", name);

  /* Get the password entry for this user. */
  while (getpwnam_r (name, &pw_resultbuf, pw_buffer, pw_buflen, &pw) != 0
         && errno == ERANGE)
    {
      errno = 0;
      pw_buflen += 256;
      pw_buffer = alloca (pw_buflen);
    }

  /* If we call another PAM module, handle the module like "sufficient".
     If it returns success, we should also return success. Else ignore
     the call. This PAM modules will not be called, if the user to
     authenticate is root.  */
  if (options.use_other_modules && (pw == NULL || pw->pw_uid != 0))
    {
      unsigned int i;

      for (i = 0; options.use_other_modules[i] != NULL; i++)
	{
	  int retval;

	  retval = __call_other_module(pamh, flags,
	  			options.use_other_modules[i],
				"pam_sm_authenticate",
				&options);

	  if (retval == PAM_SUCCESS)
	    {
	      pam_get_item (pamh, PAM_SERVICE, (void *) &service);
	      if (strcasecmp (service, "chsh") == 0 ||
		  strcasecmp (service, "chfn") == 0)
		{
		  char *p;

		  pam_get_item (pamh, PAM_AUTHTOK, (void *)&p);
		  if (p != NULL)
		    {
		      char *msg = alloca (strlen (p) + 13);
		      sprintf (msg, "PAM_AUTHTOK=%s", p);
		      pam_putenv (pamh, msg);
		    }
		}
	      return retval;
	    }
	}
    }


  /* Bail out if we cannot find the account.  */
  if (pw == NULL)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "Cannot find passwd entry for %s", name);
      /* ask for the password anyways in order to prevent guessing
         of non-existing accounts (#221233) */
      if (!ask_user && ask_password)
	__get_tokens (pamh, 0, ask_password, NULL, &password);
      return PAM_USER_UNKNOWN;
    }

  /* Get shadow entry.  */
  while (getspnam_r (pw->pw_name, &sp_resultbuf, sp_buffer,
		     sp_buflen, &sp) != 0 && errno == ERANGE)
    {
      errno = 0;
      sp_buflen += 256;
      sp_buffer = alloca (sp_buflen);
    }

  if ((pw->pw_passwd == NULL || strlen (pw->pw_passwd) == 0) ||
      (sp && strcmp (pw->pw_passwd, "x") == 0 &&
       (sp->sp_pwdp == NULL || strlen (sp->sp_pwdp) == 0)))
    {
      if (flags & PAM_DISALLOW_NULL_AUTHTOK ||
	  !options.nullok || (password != NULL && strlen (password) != 0))
	{
	  if (options.debug)
	    pam_syslog (pamh, LOG_DEBUG, "return PAM_AUTH_ERR");
	  return PAM_AUTH_ERR;
	}
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "return PAM_SUCCESS");
      return PAM_SUCCESS;
    }

  /* We had the user name and only need the password, so only ask
     for the password.  */
  if (!ask_user && ask_password)
    {
      retval = __get_tokens (pamh, 0, ask_password, NULL, &password);
      if (retval != PAM_SUCCESS)
	{
	  if (options.debug)
	    pam_syslog (pamh, LOG_DEBUG, "__get_tokens failed with %d, exit",
			retval);
	  return retval;
	}
    }

  if (password == NULL)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "Cannot get password, return PAM_AUTHTOK_RECOVERY_ERR");
      return PAM_AUTHTOK_RECOVERY_ERR;
    }

  pam_get_item (pamh, PAM_SERVICE, (void *) &service);
  if (strcasecmp (service, "chsh") == 0 ||
      strcasecmp (service, "chfn") == 0)
    {
      char *msg = alloca (strlen (password) + 13);
      sprintf (msg, "PAM_AUTHTOK=%s", password);
      pam_putenv (pamh, msg);
    }

  if (pw->pw_passwd[0] != '!')
    {
      if (sp)
	salt = strdupa (sp->sp_pwdp);
      else
	{
	  if (strcmp (pw->pw_passwd, "x") == 0)
	    __write_message (pamh, flags, PAM_TEXT_INFO,
			     _("Permissions on the password database may be too restrictive."));
	  salt = strdupa (pw->pw_passwd);
	}
    }
  else
    return PAM_PERM_DENIED;


  /* This is for HP-UX password aging (why couldn't they use shadow ?) */
  if (strchr (salt, ',') != NULL)
    {
      char *cp = alloca (strlen (salt) + 1);
      strcpy (cp, salt);
      salt = cp;
      cp = strchr (salt, ',');
      *cp = '\0';
    }

  if (strcmp (crypt_r (password, salt, &output), salt) != 0)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "wrong password, return PAM_AUTH_ERR");
      return PAM_AUTH_ERR;
    }
  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "pam_sm_authenticate: PAM_SUCCESS");
  return PAM_SUCCESS;
}

int
pam_sm_setcred (pam_handle_t *pamh, int flags, int argc, const char **argv)
{
  int retval;
  options_t options;
  int pw_buflen = 256;
  char *pw_buffer = alloca (pw_buflen);
  struct passwd pw_resultbuf;
  struct passwd *pw;
  const char *name = NULL;

  memset (&options, 0, sizeof (options));

  if (get_options (pamh, &options, "auth", argc, argv) < 0)
    {
      pam_syslog (pamh, LOG_ERR, "cannot get options");
      return PAM_SYSTEM_ERR;
    }

  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "pam_sm_setcred() called");

  /* get the user name */
  if ((retval = pam_get_user (pamh, &name, NULL)) != PAM_SUCCESS)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "pam_get_user failed: return %d", retval);
      return (retval == PAM_CONV_AGAIN ? PAM_INCOMPLETE:retval);
    }

  if (name == NULL || name[0] == '\0')
    {
      if (name)
	{
	  if (options.debug)
	    pam_syslog (pamh, LOG_ERR, "bad username [%s]", name);
	  return PAM_USER_UNKNOWN;
	}
      else if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "name == NULL, return PAM_SERVICE_ERR");
      return PAM_SERVICE_ERR;
    }
  else if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "username=[%s]", name);

  /* Get the password entry for this user. */
  while (getpwnam_r (name, &pw_resultbuf, pw_buffer, pw_buflen, &pw) != 0
         && errno == ERANGE)
    {
      errno = 0;
      pw_buflen += 256;
      pw_buffer = alloca (pw_buflen);
    }

  /* If we call another PAM module, handle the module like "sufficient".
     If it returns success, we should also return success. Else ignore
     the call. This PAM modules will not be called, if the user to
     authenticate is root.  */
  if (options.use_other_modules && (pw == NULL || pw->pw_uid != 0))
    {
      unsigned int i;

      for (i = 0; options.use_other_modules[i] != NULL; i++)
	{
	  retval = __call_other_module(pamh, flags,
				       options.use_other_modules[i],
				       "pam_sm_setcred",
				       &options);

	  if (retval != PAM_SUCCESS && retval != PAM_IGNORE &&
	      retval != PAM_CRED_UNAVAIL)
	    {
	      if (options.debug)
		pam_syslog (pamh, LOG_DEBUG, "pam_sm_setcred: %d", retval);
	      return retval;
	    }
	}
    }

  if (pw == NULL)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "Cannot find passwd entry for %s", name);
      return PAM_USER_UNKNOWN;
    }

  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "pam_sm_setcred: PAM_SUCCESS");
  return PAM_SUCCESS;
}
