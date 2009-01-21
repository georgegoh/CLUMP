/*
 * Copyright (c) 2005, 2006 SUSE LINUX Products GmbH, Nuernbeg, Germany
 * Copyright (c) 2003 SuSE Linux AG, Nuernberg, Germany
 * Copyright (c) 1999, 2000, 2001, 2002 SuSE GmbH Nuernberg, Germany
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

#include <pwd.h>
#include <time.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <shadow.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <rpc/types.h>
#include <nss.h>

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
#include "public.h"
#include "passwd_nss.h"
#include "getuser.h"

#define SCALE (24L*3600L)

void
free_user_t (user_t *data)
{
  if (data->pwdbuffer)
    free (data->pwdbuffer);
  if (data->spwbuffer)
    free (data->spwbuffer);
  if (data->newpassword)
    {
      memset (data->newpassword, 0, strlen (data->newpassword));
      free (data->newpassword);
    }
  if (data->oldpassword)
    {
      memset (data->oldpassword, 0, strlen (data->oldpassword));
      free (data->oldpassword);
    }
  if (data->oldclearpwd)
    {
      memset (data->oldclearpwd, 0, strlen (data->oldclearpwd));
      free (data->oldclearpwd);
    }
  free (data);
}

/****************************************************************/

user_t *
__do_getpwnam (const char *user, char *nisdir)
{
  enum nss_status (*nss_getpwnam_r)(const char *name, struct passwd *pwd,
				    char *buffer, size_t buflen, int *errnop);
  enum nss_status (*nss_getspnam_r)(const char *name, struct spwd *sp,
				    char *buffer, size_t buflen, int *errnop);
  enum nss_status status;
  user_t *data;
  struct nsw *nswp;
  void *nss_handle = NULL;
  int i;

  data = calloc (1, sizeof (user_t));
  if (data == NULL)
    return NULL;

  data->service = S_NONE;

  /* UNIX passwords area */

  nswp = _getnswbyname ("passwd");
  if (nswp == NULL)
    return data;

  for (i = 0; i < nswp->orderc; ++i)
    {
      const char *cmpptr = nswp->orders[i];

    again:

      if (nswp->orders[i][0] == '[')
	continue;
      if (strcmp ("files", cmpptr) == 0 || strcmp ("compat", cmpptr) == 0)
	{
#if USE_DLOPEN_FOR_FILES
	  /* We dlopen libnss_files.  */
	  nss_handle = dlopen ("libnss_files.so.2", RTLD_NOW);
	  if (!nss_handle)
	    continue;
	  nss_getpwnam_r = dlsym (nss_handle, "_nss_files_getpwnam_r");
	  if (dlerror () != NULL)
	    {
	      dlclose (nss_handle);
	      continue;
	    }
#else
	  nss_getpwnam_r = files_getpwnam_r;
#endif
	  /* Get password file entry... */
	  do {
	    data->pwdbuflen += 1024;
	    data->pwdbuffer = realloc (data->pwdbuffer, data->pwdbuflen);
	    status = (*nss_getpwnam_r)(user, &data->pwd, data->pwdbuffer,
				       data->pwdbuflen, &errno);
	  } while (status == NSS_STATUS_TRYAGAIN && errno == ERANGE);

	  if (status != NSS_STATUS_SUCCESS)
	    {
#if USE_DLOPEN_FOR_FILES
	      dlclose (nss_handle);
#endif
	      free (data->pwdbuffer);
	      data->pwdbuffer = NULL;
	      data->pwdbuflen = 0;
	      if (strcmp ("compat", cmpptr) == 0)
		{
		  struct nsw *nswp2 = _getnswbyname ("passwd_compat");

		  if (nswp2 == NULL)
		    cmpptr = "nis";
		  else
		    {
		      char *cp = alloca (strlen (nswp2->orders[0]) + 1);
		      strcpy (cp, nswp2->orders[0]);
		      cmpptr = cp;
		      nsw_free (nswp2);
		    }
		  goto again;
		}
	    }
	  else
	    {
	      data->service = S_LOCAL;
	      break;
	    }
	}
      else if (strcmp ("nis", cmpptr) == 0)
	{
	  const char *backup_etc_dir = NULL;

	  if (nisdir != NULL)
	    {
	      nss_getpwnam_r = files_getpwnam_r;
	      backup_etc_dir = files_etc_dir;
	      files_etc_dir = nisdir;
	    }
	  else
	    {
	      /* Get password NIS entry... */
	      nss_handle = dlopen ("libnss_nis.so.2", RTLD_NOW);
	      if (!nss_handle)
		continue;
	      nss_getpwnam_r = dlsym (nss_handle, "_nss_nis_getpwnam_r");
	      if (dlerror () != NULL)
		{
		  dlclose (nss_handle);
		  continue;
		}
	    }
	  do {
	    data->pwdbuflen += 1024;
	    data->pwdbuffer = realloc (data->pwdbuffer, data->pwdbuflen);
	    status = (*nss_getpwnam_r)(user, &data->pwd, data->pwdbuffer,
				       data->pwdbuflen, &errno);
	  } while (status == NSS_STATUS_TRYAGAIN && errno == ERANGE);

	  /* Restore path to passwd/shadow to default one.  */
	  if (backup_etc_dir != NULL)
	    files_etc_dir = backup_etc_dir;

	  if (status != NSS_STATUS_SUCCESS)
	    {
	      if (nss_handle)
		dlclose (nss_handle);
	      free (data->pwdbuffer);
	      data->pwdbuffer = NULL;
	      data->pwdbuflen = 0;
	    }
	  else
	    {
	      data->service = S_YP;
	      break;
	    }
	}
      else if (strcmp ("ldap", cmpptr) == 0)
	{
	  nss_handle = dlopen ("libnss_ldap.so.2", RTLD_NOW);
	  if (!nss_handle)
	    continue;
	  nss_getpwnam_r = dlsym (nss_handle, "_nss_ldap_getpwnam_r");
	  if (dlerror () != NULL)
	    {
	      dlclose (nss_handle);
	      continue;
	    }

	  /* Get password NIS entry... */
	  do {
	    data->pwdbuflen += 1024;
	    data->pwdbuffer = realloc (data->pwdbuffer, data->pwdbuflen);
	    status = (*nss_getpwnam_r)(user, &data->pwd,
				       data->pwdbuffer,
				       data->pwdbuflen, &errno);
	  } while (status == NSS_STATUS_TRYAGAIN && errno == ERANGE);

	  if (status != NSS_STATUS_SUCCESS)
	    {
	      dlclose (nss_handle);
	      free (data->pwdbuffer);
	      data->pwdbuffer = NULL;
	      data->pwdbuflen = 0;
	    }
	  else
	    {
	      data->service = S_LDAP;
	      break;
	    }
	}
    }
  nsw_free (nswp);

  if (data->service == S_NONE)
    return data;

  if (data->service == S_LOCAL)
    {
#if USE_DLOPEN_FOR_FILES
      nss_getspnam_r = dlsym (nss_handle, "_nss_files_getspnam_r");
      if (dlerror () != NULL)
	{
	  data->service = S_NONE;
	  free (data->pwdbuffer);
	  data->pwdbuffer = NULL;
	  data->pwdbuflen = 0;
	  dlclose (nss_handle);
	  return data;
	}
#else
      nss_getspnam_r = files_getspnam_r;
#endif
      do {
	data->spwbuflen += 1024;
	data->spwbuffer = realloc (data->spwbuffer, data->spwbuflen);
	status = (*nss_getspnam_r)(user, &data->spw, data->spwbuffer,
				   data->spwbuflen, &errno);
      } while (status == NSS_STATUS_TRYAGAIN && errno == ERANGE);
#if USE_DLOPEN_FOR_FILES
      dlclose (nss_handle);
#endif
    }
  else if (data->service == S_YP)
    {
      const char *backup_etc_dir = NULL;

      if (nisdir)
	{
	  nss_getspnam_r = files_getspnam_r;
	  backup_etc_dir = files_etc_dir;
	  files_etc_dir = nisdir;
	}
      else
	{
	  nss_getspnam_r = dlsym (nss_handle, "_nss_nis_getspnam_r");
	  if (dlerror () != NULL)
	    {
	      data->service = S_NONE;
	      free (data->pwdbuffer);
	      data->pwdbuffer = NULL;
	      data->pwdbuflen = 0;
	      dlclose (nss_handle);
	      return data;
	    }
	}
      do {
	data->spwbuflen += 1024;
	data->spwbuffer = realloc (data->spwbuffer, data->spwbuflen);
	status = (*nss_getspnam_r)(user, &data->spw, data->spwbuffer,
				   data->spwbuflen, &errno);
      } while (status == NSS_STATUS_TRYAGAIN && errno == ERANGE);
      if (backup_etc_dir != NULL)
	files_etc_dir = backup_etc_dir;
      if (nss_handle)
	dlclose (nss_handle);
    }
  else if (data->service == S_LDAP)
    {
      nss_getspnam_r = dlsym (nss_handle, "_nss_ldap_getspnam_r");
      if (dlerror () != NULL)
	{
	  data->service = S_NONE;
	  free (data->pwdbuffer);
	  data->pwdbuffer = NULL;
	  data->pwdbuflen = 0;
	  dlclose (nss_handle);
	  return data;
	}
      do {
	data->spwbuflen += 1024;
	data->spwbuffer = realloc (data->spwbuffer, data->spwbuflen);
	status = (*nss_getspnam_r)(user, &data->spw, data->spwbuffer,
				   data->spwbuflen, &errno);
      } while (status == NSS_STATUS_TRYAGAIN && errno == ERANGE);
      dlclose (nss_handle);
    }
  else
    status = NSS_STATUS_NOTFOUND;

  if (status == NSS_STATUS_SUCCESS)
    data->use_shadow = TRUE;
  else if (strchr (data->pwd.pw_passwd, ',') != NULL)
    {
      char *age = strchr (data->pwd.pw_passwd, ',');
      long now = time (NULL) / (SCALE * 7);

      data->use_hp_aging = TRUE;
      *age++ = '\0';
      data->hp_max = c2n (age[0]);
      ++age;
      data->hp_min = c2n (age[0]);
      ++age;
      data->hp_week = str2week (age);

      if (data->hp_min > 0 && now <= (data->hp_week + data->hp_min))
	data->is_tooearly = TRUE;
      else if ((data->hp_max == 0 && data->hp_min == 0) ||
	       ((now > data->hp_week + data->hp_max) &&
		(data->hp_max >= data->hp_min)))
	data->is_expiring = TRUE;
    }

  if (data->use_shadow &&
      data->pwd.pw_passwd && data->pwd.pw_passwd[0] != '!')
    {
      long now = time (NULL) / SCALE;

      data->oldpassword = strdup (data->spw.sp_pwdp);

      if (data->spw.sp_lstchg > 0)
	{
	  if (data->spw.sp_min > 0 &&
	      now <= (data->spw.sp_lstchg + data->spw.sp_min))
	    data->is_tooearly = TRUE;
	  else if (data->spw.sp_inact >= 0 && data->spw.sp_max >= 0 &&
		   now >= (data->spw.sp_lstchg + data->spw.sp_max +
			   data->spw.sp_inact))
	    data->is_expired = TRUE;
	  else if (data->spw.sp_max >= 0 &&
		   now >= (data->spw.sp_lstchg + data->spw.sp_max))
	    data->is_expiring = TRUE;
	}
      else if (data->spw.sp_lstchg == 0)
	data->is_expiring = TRUE;
    }
  else
    {
      char *cp;

      data->oldpassword = strdup (data->pwd.pw_passwd);
      cp = strchr (data->oldpassword, ',');
      if (cp != NULL)
	*cp = '\0';
    }

  return data;
}

/* prompt user for a using conversation calls */
int
__get_passwd (pam_handle_t *pamh, const char *msgs, char **passwd)
{
  int retval;
#if defined (HAVE_PAM_PROMPT)
  char *resp = NULL;

  *passwd = NULL;

  retval = pam_prompt (pamh, PAM_PROMPT_ECHO_OFF, &resp, msgs);

  if (retval != PAM_SUCCESS)
    {
      _pam_drop (resp);
      if (retval == PAM_CONV_AGAIN)
	retval = PAM_INCOMPLETE;
      return retval;
    }

  *passwd = resp;

#else
  struct pam_message msg[1], *pmsg[1];
  struct pam_response *resp;
  struct pam_conv *conv;
  void *conv_void;

  /* set up conversation call */

  pmsg[0] = &msg[0];
  msg[0].msg_style = PAM_PROMPT_ECHO_OFF;
  msg[0].msg = msgs;
  resp = NULL;


  retval = pam_get_item (pamh, PAM_CONV, (const void **)&conv_void);
  conv = (struct pam_conv *) conv_void;
  if (retval == PAM_SUCCESS)
    {
      retval = conv->conv (1, (const struct pam_message **)pmsg,
                           &resp, conv->appdata_ptr);
      if (retval == PAM_CONV_AGAIN)
	retval = PAM_INCOMPLETE;
      if (retval != PAM_SUCCESS)
        return retval;
    }
  else
    return retval;

  if (resp)
    {
      if (resp->resp)
        *passwd = strdup (resp->resp);
      else
        *passwd = NULL;
      _pam_drop_reply (resp, 1);
    }
  else
    return PAM_CONV_ERR;

#endif

  return PAM_SUCCESS;
}
