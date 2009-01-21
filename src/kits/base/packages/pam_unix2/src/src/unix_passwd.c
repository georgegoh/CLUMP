/*
 * Copyright (c) 2006 SuSE Linux Products GmbH, Germany.
 * Copyright (c) 1999-2004 SuSE Linux AG, Germany.
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
#include "config.h"
#endif

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pwd.h>
#include <shadow.h>
#include <dlfcn.h>
#include <time.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <rpc/types.h>
#include <nss.h>
#include <syslog.h>
#include <rpcsvc/yp_prot.h>
#include <rpcsvc/ypclnt.h>

#define PAM_SM_PASSWORD
#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#if defined(HAVE_XCRYPT_H)
#include <xcrypt.h>
#elif defined(HAVE_CRYPT_H)
#include <crypt.h>
#endif

#include "read-files.h"
#include "yppasswd.h"
#include "public.h"
#include "passwd_nss.h"
#include "getuser.h"
#include "logindefs.h"

#ifndef RANDOM_DEVICE
#define RANDOM_DEVICE "/dev/urandom"
#endif

#define MAX_LOCK_RETRIES 3 /* How often should we try to lock password file */
#define OLD_PASSWORD_PROMPT _("Old Password: ")
#define NEW_PASSWORD_PROMPT _("New Password: ")
#define AGAIN_PASSWORD_PROMPT _("Reenter New Password: ")

#define SCALE (24L*3600L)

static int __do_setpass (pam_handle_t *pamh, int flags, user_t *user,
			 options_t *options, struct crypt_data *output);

PAM_EXTERN int
pam_sm_chauthtok (pam_handle_t *pamh, int flags, int argc, const char **argv)
{
  struct crypt_data output;
  user_t *data;
  const char *name = NULL;
  char *oldpass, *newpass;
  /* The following variables are needed to avoid dereferencing
     type-punned pointer warings.  */
  void *oldpass_void, *newpass_void;
  int retval;
  options_t options;

  memset (&output, 0, sizeof (output));
  memset (&options, 0, sizeof (options));

  if (get_options (pamh, &options, "password", argc, argv) < 0)
    {
      pam_syslog (pamh, LOG_ERR, "cannot get options");
      return PAM_SYSTEM_ERR;
    }

  if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "pam_sm_chauthtok() called");

  /* get the user name */
  if ((retval = pam_get_user (pamh, &name, NULL)) != PAM_SUCCESS)
    {
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG,
		    "pam_get_user failed: return %d", retval);
      return (retval == PAM_CONV_AGAIN ? PAM_INCOMPLETE:retval);
    }

  if (name == NULL || name[0] == '\0')
    {
      if (name)
	{
	  pam_syslog (pamh, LOG_ERR, "bad username [%s]", name);
	  return PAM_USER_UNKNOWN;
	}
      else if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "name == NULL, return PAM_SERVICE_ERR");
      return PAM_SERVICE_ERR;
    }
  else if (options.debug)
    pam_syslog (pamh, LOG_DEBUG, "username=[%s]", name);

  /* If we use ldap, handle pam_ldap like "sufficient". If it returns
     success, we should also return success. Else ignore the call.  */
  if (options.use_other_modules)
    {
      unsigned int i;

      for (i = 0; options.use_other_modules[i] != NULL; i++)
	{
	  int retval;

	  retval = __call_other_module (pamh, flags,
	  			options.use_other_modules[i],
				"pam_sm_chauthtok",
				&options);
	  if (retval == PAM_SUCCESS)
	    return retval;
	}
    }

  data = __do_getpwnam (name, options.nisdir);
  if (data == NULL || data->service == S_NONE)
    {
      if (data)
	free_user_t (data);
      return PAM_USER_UNKNOWN;
    }

  /* Before we do anything else, check to make sure that the user's
     info is in one of the databases we can modify from this module,
     which currently is 'files' and 'nis'. */
  if (data->service != S_LOCAL && data->service != S_YP)
    {
      free_user_t (data);
      pam_syslog (pamh, LOG_DEBUG,
		  "user \"%s\" does not exist in /etc/passwd or NIS",
		  name);
      return PAM_USER_UNKNOWN;
    }

  retval = pam_get_item (pamh, PAM_OLDAUTHTOK, (const void **) &oldpass_void);
  oldpass = (char *)oldpass_void;
  if (retval != PAM_SUCCESS)
    {
      free_user_t (data);
      return retval;
    }

  if (oldpass == NULL)
    {
      /* If this is being run by root and we change a local password,
	 we don't need to get the old password. The test for
	 PAM_CHANGE_EXPIRED_AUTHTOK is here, because login runs as
         root and we need the old password in this case.  */
      if (options.debug)
	pam_syslog (pamh, LOG_DEBUG, "No old password found.");

      /* Ask for old password: if we are a normal user or if
	 we are called by login or if we are not a local user.
	 If we are a NIS user, but called by root for on the
	 master, change local password with query, too.  */
      if (getuid () || (flags & PAM_CHANGE_EXPIRED_AUTHTOK) ||
	  (data->service != S_LOCAL &&
	   !(data->service == S_YP && options.nisdir != NULL )))
	{
	  char *tmp_oldpass;

	  if (options.use_first_pass)
	    {
	      if (options.debug)
		pam_syslog (pamh, LOG_DEBUG, "use_first_pass set -> abort.");

	      free_user_t (data);
	      if (getuid () == 0 && data->service != S_LOCAL)
		__write_message (pamh, flags, PAM_ERROR_MSG,
				 _("You can only change local passwords."));
	      return PAM_AUTHTOK_RECOVERY_ERR;
	    }

	  retval = __get_passwd (pamh, OLD_PASSWORD_PROMPT, &tmp_oldpass);
	  if (retval != PAM_SUCCESS)
	    {
	      free_user_t (data);
	      return retval;
	    }

	  if (tmp_oldpass == NULL)
	    {
	      if (options.debug)
		pam_syslog (pamh, LOG_DEBUG,
			    "old password is NULL -> abort.");
	      free_user_t (data);
	      return PAM_AUTH_ERR;
	    }

	  oldpass = strdupa (tmp_oldpass);
	  free (tmp_oldpass);

	  /* Empty password means: entry is locked */
	  if ((data->oldpassword == NULL || strlen (data->oldpassword) == 0)
	      && !options.nullok)
	    {
	      if (options.debug)
		pam_syslog (pamh, LOG_DEBUG,
		      "old password is empty which is not allowed -> abort.");
	      free_user_t (data);
	      return PAM_AUTH_ERR;
	    }

	  pam_set_item (pamh, PAM_OLDAUTHTOK, (void *) oldpass);
	}
      else
	oldpass = "";
    }

  if (flags & PAM_PRELIM_CHECK)
    {
      /* Check if the old password was correct.  */
      if ((getuid () || (flags & PAM_CHANGE_EXPIRED_AUTHTOK)) && strcmp (data->oldpassword,
			crypt_r (oldpass, data->oldpassword, &output)) != 0)
	{
	  if (options.debug)
	    pam_syslog (pamh, LOG_DEBUG,
			"old password is wrong -> abort.");

	  retval = PAM_AUTH_ERR;
	}
      else if (data->is_expired)
	retval = PAM_ACCT_EXPIRED;
      else
	retval = PAM_SUCCESS;

      free_user_t (data);
      return retval;
    }


  /* Now we have all the initial information we need from the app to
     set things up (we assume that getting the username succeeded...) */
  if ((flags & PAM_CHANGE_EXPIRED_AUTHTOK) || getuid () != 0)
    {
      if (data->is_tooearly)
	{
	  if (data->use_hp_aging)
	    __write_message (pamh, flags, PAM_TEXT_INFO,
			     _("Less then %d weeks since the last change."),
			     data->hp_week);
	  else
	    __write_message (pamh, flags, PAM_TEXT_INFO,
			     _("Less then %d days since the last change."),
			     data->spw.sp_min);
	  free_user_t (data);
	  return PAM_AUTHTOK_ERR;
	}
      else if (data->is_expired)
	{
	  free_user_t (data);
	  return PAM_ACCT_EXPIRED; /* If their account has expired, we
				      can't auth them to change their
				      password */
	}
    }

  if ((data->use_shadow || data->use_hp_aging) && !data->is_expiring &&
      (flags & PAM_CHANGE_EXPIRED_AUTHTOK))
    {
      free_user_t (data);
      return PAM_SUCCESS;
    }

  /* create a copy which we can give free later */
  data->oldclearpwd = strdup (oldpass);

  /* If we haven't been given a password yet, prompt for one... */
  pam_get_item (pamh, PAM_AUTHTOK, (const void **) &newpass_void);
  newpass = (char *)newpass_void;
  if (newpass != NULL)
    newpass = strdup (newpass);

  if (newpass == NULL)
    {
      char *new2;

      if (options.use_authtok)
	{
	  free_user_t (data);
	  return PAM_AUTHTOK_ERR; /* We are not allowed to ask for a
				     new password. */
	}

      retval = __get_passwd (pamh, NEW_PASSWORD_PROMPT, &newpass);
      if (retval != PAM_SUCCESS)
	{
	  free_user_t (data);
	  return retval;
	}

      if (newpass == NULL)
	{
	  /* We want to abort the password change */
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Password change aborted."));
	  free_user_t (data);
	  return PAM_AUTHTOK_ERR;
	}

      retval = __get_passwd (pamh, AGAIN_PASSWORD_PROMPT, &new2);
      if (retval != PAM_SUCCESS)
	{
	  free_user_t (data);
	  return retval;
	}

      if (new2 == NULL)
	{			/* Aborting password change... */
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Password change aborted."));
	  free_user_t (data);
	  return PAM_AUTHTOK_ERR;
	}

      if (strcmp (newpass, new2) == 0)
	{
	  memset (new2, '\0', strlen (new2));
	  free (new2);
	  new2 = NULL;
	}
      else
	{
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Passwords do not match."));
	  if (new2 != NULL)
	    {
	      memset (new2, '\0', strlen (new2));
	      free (new2);
	      new2 = NULL;
	    }
	  if (newpass != NULL)
	    {
	      memset (newpass, '\0', strlen (newpass));
	      free (newpass);
	      newpass = NULL;
	    }
	  free_user_t (data);
	  return PAM_AUTHTOK_ERR; /* user have to call passwd again. */
	}
    }
  /* end if (newpass == NULL) */

  data->newpassword = newpass;
  retval = __do_setpass (pamh, flags, data, &options, &output);
  if (retval != PAM_SUCCESS)
    {
      free_user_t (data);
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("Error: Password NOT changed."));
      return retval;
    }
  else
    {
      pam_set_item (pamh, PAM_AUTHTOK, (void *) newpass);

      free_user_t (data);
      __write_message (pamh, flags, PAM_TEXT_INFO, _("Password changed."));
      return PAM_SUCCESS;
    }
}

static char *
getnismaster (pam_handle_t *pamh, int flags)
{

  char *master, *domainname;
  int port, err;

  yp_get_default_domain (&domainname);

  if ((err = yp_master (domainname, "passwd.byname", &master)) != 0)
    {
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("Cannot find the master ypserver: %s"),
		       yperr_string (err));
      return NULL;
    }
  port = getrpcport (master, YPPASSWDPROG, YPPASSWDPROC_UPDATE, IPPROTO_UDP);
  if (port == 0)
    {
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("yppasswdd not running on NIS master %s"), master);
      return NULL;
    }
  if (port >= IPPORT_RESERVED)
    {
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("yppasswd daemon running on illegal port."));
      return NULL;
    }

  return master;
}

#if defined(HAVE_XCRYPT_GENSALT_R)
static int
read_loop (int fd, char *buffer, int count)
{
  int offset, block;

  offset = 0;
  while (count > 0)
    {
      block = read(fd, &buffer[offset], count);

      if (block < 0)
	{
	  if (errno == EINTR)
	    continue;
	  return block;
	}
      if (!block)
	return offset;

      offset += block;
      count -= block;
    }

  return offset;
}

#endif

static char *
make_crypt_salt (const char *crypt_prefix, int crypt_rounds,
		 pam_handle_t *pamh, int flags)
{
#if defined(HAVE_XCRYPT_GENSALT_R)
#define CRYPT_GENSALT_OUTPUT_SIZE (7 + 22 + 1)
  int fd;
  char entropy[16];
  char *retval;
  char output[CRYPT_GENSALT_OUTPUT_SIZE];

  fd = open (RANDOM_DEVICE, O_RDONLY);
  if (fd < 0)
    {
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("Cannot open %s for reading: %s"),
		       RANDOM_DEVICE, strerror (errno));
      return NULL;
    }

  if (read_loop (fd, entropy, sizeof(entropy)) != sizeof(entropy))
    {
      close (fd);
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("Unable to obtain entropy from %s"),
		       RANDOM_DEVICE);
      return NULL;
    }

  close (fd);

  retval = xcrypt_gensalt_r (crypt_prefix, crypt_rounds, entropy,
			     sizeof (entropy), output, sizeof(output));

  memset (entropy, 0, sizeof (entropy));

  if (!retval)
    {
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("Unable to generate a salt. "
			 "Check your crypt settings."));
      return NULL;
    }

  return strdup (retval);
#else
#define ascii_to_bin(c) ((c)>='a'?(c-59):(c)>='A'?((c)-53):(c)-'.')
#define bin_to_ascii(c) ((c)>=38?((c)-38+'a'):(c)>=12?((c)-12+'A'):(c)+'.')

  time_t tm;
  char salt[3];

  time (&tm);
  salt[0] = bin_to_ascii(tm & 0x3f);
  salt[1] = bin_to_ascii((tm >> 6) & 0x3f);
  salt[2] = '\0';

  return strdup (salt);
#endif
}

static int
__do_setpass (pam_handle_t *pamh, int flags, user_t *data,
	      options_t *options, struct crypt_data *output)
{
  int retval = PAM_SUCCESS;
  char *salt;
  char *newpassword = NULL;

  if (options->use_crypt == NONE)
    {
      const char *crypt_str = NULL;
      char *opt_str = NULL;

      switch (data->service)
	{
	case S_LOCAL:
	  opt_str = "CRYPT_FILES";
	  crypt_str = getlogindefs_str (opt_str, NULL);
	  break;
	case S_YP:
	  opt_str = "CRYPT_YP";
	  crypt_str = getlogindefs_str (opt_str, NULL);
	  if (crypt_str == NULL)
	    {
	      opt_str = "CRYPT_NIS";
	      crypt_str = getlogindefs_str (opt_str, NULL);
	    }
	  break;
	case S_LDAP:
	  opt_str = "CRYPT_LDAP";
	  crypt_str = getlogindefs_str (opt_str, NULL);
	  break;
	default:
	  break;
	}

      if (crypt_str == NULL)
	{
	  opt_str = "CRYPT";
	  crypt_str = getlogindefs_str (opt_str, "DES");
	}

      if (strcasecmp (crypt_str, "des") == 0)
	options->use_crypt = DES;
      else if (strcasecmp (crypt_str, "md5") == 0)
	options->use_crypt = MD5;
      else if (strcasecmp (crypt_str, "bigcrypt") == 0)
	{
#if defined(HAVE_BIGCRYPT)
	  options->use_crypt = BIGCRYPT;
#else
	  pam_syslog (pamh, LOG_ERR, "No bigcrypt support compiled in");
#endif
	}
      else if (strcasecmp (crypt_str, "bf") == 0 ||
	       strcasecmp (crypt_str, "blowfish") == 0)
	{
#if defined(HAVE_XCRYPT_GENSALT_R)
	  const char *round;
	  char *cp;

	  options->use_crypt = BLOWFISH;
	  if (asprintf (&cp, "BLOWFISH_%s", opt_str) > 0)
	    {
	      round = getlogindefs_str (cp, NULL);
	      free (cp);
	      if (round)
		options->crypt_rounds = atoi (round); /* XXX strtol */
	    }
	  if (options->debug)
	    pam_syslog (pamh, LOG_DEBUG, "Blowfish crypt_rounds=%d",
			options->crypt_rounds);
#else
	  pam_syslog (pamh, LOG_ERR, "No blowfish support compiled in");
#endif
	}
      else
	{
	  pam_syslog (pamh, LOG_ERR,
		      "Don't know \"%s\", fall back to DES", crypt_str);
	  options->use_crypt = DES;
	}
      free_getlogindefs_data ();
    }

  /* If we don't support passwords longer 8 characters, truncate them */
  if (options->use_crypt == DES && strlen (data->newpassword) > 8)
    data->newpassword[8] = '\0';
  /* blowfish has a limit of 72 characters */
  if (options->use_crypt == BLOWFISH && strlen (data->newpassword) > 72)
    data->newpassword[72] = '\0';
  /* MD5 has a limit of 127 characters */
  if (options->use_crypt == MD5 && strlen (data->newpassword) > 127)
    data->newpassword[127] = '\0';

  switch (options->use_crypt)
    {
    case DES:
      salt =  make_crypt_salt ("", 0, pamh, flags);
      if (salt != NULL)
	newpassword = crypt_r (data->newpassword, salt, output);
      else
	{
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Cannot create salt for standard crypt"));
	  return PAM_AUTHTOK_ERR;
	}
      free (salt);
      break;
    case MD5:
      salt = make_crypt_salt ("$1$", 0, pamh, flags);
      if (salt != NULL)
	newpassword = crypt_r (data->newpassword, salt, output);
      else
	{
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Cannot create salt for MD5 crypt"));
	  return PAM_AUTHTOK_ERR;
	}
      free (salt);
      break;
    case BIGCRYPT:
#if defined (HAVE_BIGCRYPT)
      salt = make_crypt_salt ("", 0, pamh, flags);
      if (salt != NULL)
	newpassword = bigcrypt (data->newpassword, salt);
      else
	{
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Cannot create salt for bigcrypt"));
	  return PAM_AUTHTOK_ERR;
	}
      free (salt);
#else
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("No support for bigcrypt included"));
      return PAM_AUTHTOK_ERR;
#endif
      break;
    case BLOWFISH:
#if defined(HAVE_XCRYPT_GENSALT_R)
      salt = make_crypt_salt ("$2a$", options->crypt_rounds, pamh, flags);
      if (salt != NULL)
	newpassword = crypt_r (data->newpassword, salt, output);
      else
	{
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Cannot create salt for blowfish crypt"));
	  return PAM_AUTHTOK_ERR;
	}
      free (salt);
#else
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("No support for blowfish included"));
      return PAM_AUTHTOK_ERR;
#endif
      break;
    default:
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       "crypt_r: Don't know %d", options->use_crypt);
      return PAM_AUTHTOK_ERR;
    }
  if (newpassword == NULL)
    {
      __write_message (pamh, flags, PAM_ERROR_MSG,
		       _("crypt_r() returns NULL pointer"));
      return PAM_AUTHTOK_ERR;
    }

  if (data->service == S_LOCAL || (data->service == S_YP && options->nisdir))
    {
      int retries = 0;
      const char *etcdir;

      if (options->nisdir && data->service == S_YP)
	etcdir = options->nisdir;
      else
	etcdir = files_etc_dir;

      while (lckpwdf () && retries < MAX_LOCK_RETRIES)
        {
          sleep (1);
          ++retries;
        }

      if (retries == MAX_LOCK_RETRIES)
        {
	  __write_message (pamh, flags, PAM_ERROR_MSG,
			   _("Cannot lock password file: already locked."));
	  retval = PAM_AUTHTOK_LOCK_BUSY;
        }
      else if (data->use_shadow)
	{
	  const char *fn_shadow_tmp = "/shadow.tmpXXXXXX";
	  const char *fn_shadow_orig = "/shadow";
	  char *shadow_tmp =
	    alloca (strlen (etcdir) + strlen (fn_shadow_tmp) + 2);
	  char *shadow_orig =
	    alloca (strlen (etcdir) + strlen (fn_shadow_orig) + 2);
	  char *shadow_old =
	    alloca (strlen (etcdir) + strlen (fn_shadow_orig) + 6);
	  struct stat passwd_stat;
	  struct spwd *sp; /* shadow struct obtained from fgetspent() */
	  FILE *oldpf, *newpf;
	  int gotit, newpf_fd;

	  sprintf (shadow_tmp, "%s%s", etcdir, fn_shadow_tmp);
	  sprintf (shadow_orig, "%s%s", etcdir, fn_shadow_orig);
	  sprintf (shadow_old, "%s%s.old", etcdir, fn_shadow_orig);

	  /* Open the shadow file for reading. We can't use getspent and
	     friends here, because they go through the YP maps, too. */
	  if ((oldpf = fopen (shadow_orig, "r")) == NULL)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot open %s: %m"), shadow_orig);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_shadow;
	    }
	  if (fstat (fileno (oldpf), &passwd_stat) < 0)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot stat %s: %m"), shadow_orig);
	      fclose (oldpf);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_shadow;
	    }

#ifdef WITH_SELINUX
          security_context_t prev_context;
          if (set_default_context (pamh, shadow_orig, &prev_context) < 0)
            {
              fclose (oldpf);
              retval = PAM_AUTHTOK_ERR;
              goto error_shadow;
            }
#endif
	  /* Open a temp shadow file */
	  newpf_fd = mkstemp (shadow_tmp);
#ifdef WITH_SELINUX
          if (restore_default_context (pamh, prev_context) < 0)
	    {
	      fclose (oldpf);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_shadow;
	    }
#endif
	  if (newpf_fd == -1)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot create temp file (%s): %m"),
			       shadow_tmp);
	      fclose (oldpf);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_shadow;
	    }
	  if (fchmod (newpf_fd, passwd_stat.st_mode) == -1)
	    __write_message (pamh, flags, PAM_ERROR_MSG,
			     _("Cannot change permssions of %s: %m"),
			     shadow_tmp);
	  if (fchown (newpf_fd, passwd_stat.st_uid,
		      passwd_stat.st_gid) == -1)
	    __write_message (pamh, flags, PAM_ERROR_MSG,
			     _("Cannot change owner/group of %s: %m"),
			     shadow_tmp);
          if (copy_xattr (pamh, shadow_orig, shadow_tmp) > 0)
            {
              fclose (oldpf);
              close (newpf_fd);
              retval = PAM_AUTHTOK_ERR;
              goto error_shadow;
            }
	  newpf = fdopen (newpf_fd, "w+");
	  if (newpf == NULL)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot open %s: %m"),
			       shadow_tmp);
	      fclose (oldpf);
	      close (newpf_fd);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_shadow;
	    }

	  gotit = 0;

	  /* Loop over all passwd entries */
	  while ((sp = fgetspent (oldpf)) != NULL)
	    {
	      /* check if this is the uid we want to change. A few
		 sanity checks added for consistency. */
	      if (!gotit && strcmp (data->pwd.pw_name, sp->sp_namp) == 0)
		{
		  time_t now;

		  time(&now);
		  /* set the new passwd */
		  sp->sp_pwdp = newpassword;
		  sp->sp_lstchg = (long int)now / (24L*3600L);
		  gotit = 1;
		}

	      /* write the passwd entry to tmp file */
	      if (putspent (sp, newpf) < 0)
		{
		  __write_message (pamh, flags, PAM_ERROR_MSG,
				   _("Error while writing new shadow file: %m"));
		  fclose (oldpf);
		  fclose (newpf);
		  retval = PAM_AUTHTOK_ERR;
		  goto error_shadow;
		}
	    }
          if (fclose (oldpf) != 0)
            {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Error while closing old shadow file: %m"));
              fclose (newpf);
              retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }
          if (fclose (newpf) != 0)
            {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Error while closing temporary shadow file: %m"));
              retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }
	  unlink (shadow_old);
	  if (link (shadow_orig, shadow_old) == -1)
	    __write_message (pamh, flags,PAM_ERROR_MSG,
			     _("Cannot create backup file of %s: %m"),
			     shadow_orig);
	  rename (shadow_tmp, shadow_orig);
	error_shadow:
	  unlink (shadow_tmp);
	}
      else
	{
	  const char *fn_passwd_tmp = "/passwd.tmpXXXXXX";
	  const char *fn_passwd_orig = "/passwd";
	  char *passwd_orig =
	    alloca (strlen (etcdir) + strlen (fn_passwd_orig) + 2);
	  char *passwd_old =
	    alloca (strlen (etcdir) + strlen (fn_passwd_orig) + 6);
	  char *passwd_tmp =
	    alloca (strlen (etcdir) + strlen (fn_passwd_tmp) + 2);
	  struct stat passwd_stat;
	  struct passwd *pw; /* passwd struct obtained from fgetpwent() */
	  FILE *oldpf, *newpf;
	  int gotit, newpf_fd;

	  sprintf (passwd_tmp, "%s%s", etcdir, fn_passwd_tmp);
	  sprintf (passwd_orig, "%s%s", etcdir, fn_passwd_orig);
	  sprintf (passwd_old, "%s%s.old", etcdir, fn_passwd_orig);

	  if ((oldpf = fopen (passwd_orig, "r")) == NULL)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot open %s: %m"), passwd_orig);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_passwd;
	    }
          if (fstat (fileno (oldpf), &passwd_stat) < 0)
            {
              __write_message (pamh, flags, PAM_ERROR_MSG,
                               _("Cannot stat %s: %m"), passwd_orig);
              fclose (oldpf);
	      retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }

#ifdef WITH_SELINUX
          security_context_t prev_context;
          if (set_default_context (pamh, passwd_orig, &prev_context) < 0)
            {
              fclose (oldpf);
              retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }
#endif
	  /* Open a temp passwd file */
	  newpf_fd = mkstemp (passwd_tmp);
#ifdef WITH_SELINUX
          if (restore_default_context (pamh, prev_context) < 0)
	    {
	      fclose (oldpf);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_passwd;
	    }
#endif
	  if (newpf_fd == -1)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot create temp file (%s): %m"),
			       passwd_tmp);
	      fclose (oldpf);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_passwd;
	    }
          if (fchmod (newpf_fd, passwd_stat.st_mode) == -1)
	    __write_message (pamh, flags, PAM_ERROR_MSG,
                             _("Cannot change permssions of %s: %m"),
			     passwd_tmp);
          if (fchown (newpf_fd, passwd_stat.st_uid, passwd_stat.st_gid) == -1)
	    __write_message (pamh, flags, PAM_ERROR_MSG,
                             _("Cannot change owner/group of %s: %m"),
                             passwd_tmp);
          if (copy_xattr (pamh, passwd_orig, passwd_tmp) > 0)
            {
              fclose (oldpf);
              close (newpf_fd);
              unlink (passwd_tmp);
              retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }
	  newpf = fdopen (newpf_fd, "w+");
	  if (newpf == NULL)
	    {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Cannot open %s: %m"), passwd_tmp);
	      fclose (oldpf);
	      close (newpf_fd);
	      retval = PAM_AUTHTOK_ERR;
	      goto error_passwd;
	    }

	  gotit = 0;

	  /* Loop over all passwd entries */
	  while ((pw = fgetpwent (oldpf)) != NULL)
	    {
	      /* check if this is the uid we want to change. A few
		 sanity checks added for consistency. */
	      if (data->pwd.pw_uid == pw->pw_uid &&
		  data->pwd.pw_gid == pw->pw_gid &&
		  !strcmp (data->pwd.pw_name, pw->pw_name) && !gotit)
		{
		  pw->pw_passwd = newpassword;
		  gotit = 1;
		}

	      /* write the passwd entry to tmp file */
	      if (putpwent (pw, newpf) < 0)
		{
		  __write_message (pamh, flags, PAM_ERROR_MSG,
				   _("Error while writing new password file: %m"));
		  fclose (oldpf);
		  fclose (newpf);
		  retval = PAM_AUTHTOK_ERR;
		  goto error_passwd;
		}
	    }
          if (fclose (oldpf) != 0)
            {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Error while closing old password file: %m"));
              fclose (newpf);
              retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }
          if (fclose (newpf) != 0)
            {
	      __write_message (pamh, flags, PAM_ERROR_MSG,
			       _("Error while closing temporary password file: %m"));
              retval = PAM_AUTHTOK_ERR;
              goto error_passwd;
            }
	  unlink (passwd_old);
	  if (link (passwd_orig, passwd_old) == -1)
	    __write_message (pamh, flags,PAM_ERROR_MSG,
			     _("Cannot create backup file of %s: %m"),
			     passwd_orig);
	  rename (passwd_tmp, passwd_orig);
	error_passwd:
	  unlink (passwd_tmp);
	}

      ulckpwdf ();
    }
  else if (data->service == S_YP)
    {
      struct yppasswd yppwd;
      CLIENT *clnt;
      char *master = getnismaster(pamh, flags);
      struct timeval TIMEOUT = {25, 0}; /* total timeout */
      int error, status;

      if (master == NULL)
	return PAM_AUTHTOK_ERR;

      /* Initialize password information */
      memset (&yppwd, '\0', sizeof (yppwd));
      yppwd.newpw.pw_passwd = newpassword;
      yppwd.newpw.pw_name = data->pwd.pw_name;
      yppwd.newpw.pw_uid = data->pwd.pw_uid;
      yppwd.newpw.pw_gid = data->pwd.pw_gid;
      yppwd.newpw.pw_gecos = data->pwd.pw_gecos;
      yppwd.newpw.pw_dir = data->pwd.pw_dir;
      yppwd.newpw.pw_shell = data->pwd.pw_shell;
      yppwd.oldpass = data->oldclearpwd;

      __write_message (pamh, flags, PAM_TEXT_INFO,
		       _("Changing NIS password for %s on %s."),
		       data->pwd.pw_name, master);

      clnt = clnt_create (master, YPPASSWDPROG, YPPASSWDVERS, "udp");
      clnt->cl_auth = authunix_create_default ();
      memset (&status, '\0', sizeof (status));
      error = clnt_call (clnt, YPPASSWDPROC_UPDATE,
			 (xdrproc_t) xdr_yppasswd, (caddr_t) &yppwd,
			 (xdrproc_t) xdr_int, (caddr_t) &status, TIMEOUT);
      if (error || status)
	{
	  if (error)
	    clnt_perrno (error);
	  else
	    __write_message (pamh, flags, PAM_ERROR_MSG,
			     _("Error while changing the NIS password."));
	  retval = PAM_AUTHTOK_ERR;
	}
    }

  return retval;
}
