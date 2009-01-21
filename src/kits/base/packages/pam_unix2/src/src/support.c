/*
 * Copyright (c) 2006 SUSE Linux Products GmbH Nuernberg, Germany
 * Copyright (c) 1999-2004 SuSE GmbH Nuernberg, Germany.
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

#include <config.h>

#include <stdarg.h>
#include <stdio.h>
#include <syslog.h>
#include <unistd.h>
#include <dlfcn.h>
#include <string.h>
#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#include "public.h"

int
c2n (char c)
{
  if (c == '.')
    return 0;
  else if (c == '/')
    return 1;
  else if (c >= '0' && c <= '9')
    return 2 + (c - '0');
  else if (c >= 'A' && c <= 'Z')
    return 12 + (c - 'A');
  else if (c >= 'a' && c <= 'z')
    return 38 + (c - 'a');
  else return -1;
}

long
str2week (char *date)
{
  if (date == NULL || strlen (date) == 0)
    return -1;

  if (strlen (date) == 1)
    return c2n (date[0]);
  else
    return c2n (date[0]) + (c2n (date[1]) * 64);
}

/* write message to user */
int
__write_message (pam_handle_t *pamh, int flags, int msg_style,
		 const char *fmt,...)
{
  va_list ap;
  int retval;
#if defined (HAVE_PAM_VPROMPT)
  va_start (ap, fmt);
  retval = pam_vprompt (pamh, msg_style, NULL, fmt, ap);
  va_end (ap);
#else
  struct pam_message msg[1], *pmsg[1];
  struct pam_response *resp=NULL;
  struct pam_conv *conv;
  void *conv_void;
  char buffer[512];

  va_start (ap, fmt);
  vsnprintf (buffer, sizeof (buffer), fmt, ap);
  va_end (ap);

  pmsg[0] = &msg[0];
  msg[0].msg_style = msg_style;
  msg[0].msg = buffer;

  retval = pam_get_item (pamh, PAM_CONV, (const void **) &conv_void);
  conv = (struct pam_conv *) conv_void;
  if (retval == PAM_SUCCESS)
    {
      retval = conv->conv (1, (const struct pam_message **)pmsg,
			   &resp, conv->appdata_ptr);
      if (retval != PAM_SUCCESS)
	return retval;
    }
  else
    return retval;

  msg[0].msg = NULL;
  if (resp)
    _pam_drop_reply(resp, 1);
#endif

  return retval;
}

/* prompt user for a using conversation calls */
int
__get_tokens (pam_handle_t *pamh, int ask_user, int ask_password,
	      const char **name, const char **password)
{
  int retval;

  if (ask_password && ask_user)
    {
      struct pam_message msg[2], *pmsg[2];
      struct pam_response *resp = NULL;
      struct pam_conv *conv;
      void *conv_void;
      int num_msg = 0;

      /* set up conversation call */

      retval = pam_get_item(pamh, PAM_USER, (const void **)&conv_void);
      if (retval != PAM_SUCCESS || conv_void == NULL)
	{

	  const void *promptp;
	  const char *prompt;

	  retval = pam_get_item (pamh, PAM_USER_PROMPT, &promptp);
	  if (retval != PAM_SUCCESS || promptp == NULL)
	    prompt = _("login: ");
	  else
	    prompt = promptp;

	  pmsg[num_msg] = &msg[num_msg];
	  msg[num_msg].msg_style = PAM_PROMPT_ECHO_ON;
	  msg[num_msg].msg = prompt;
	  ++num_msg;
	}
      else
	*name = conv_void;

      pmsg[num_msg] = &msg[num_msg];
      msg[num_msg].msg_style = PAM_PROMPT_ECHO_OFF;
      msg[num_msg].msg = _("Password: ");
      ++num_msg;

      retval = pam_get_item (pamh, PAM_CONV, (const void **) &conv_void);
      conv = (struct pam_conv *) conv_void;
      if (retval == PAM_SUCCESS)
	{
	  retval = conv->conv (num_msg, (const struct pam_message **)pmsg,
			       &resp, conv->appdata_ptr);
	  if (retval != PAM_SUCCESS)
	    return retval;
	}
      else
	return retval;

      if (resp)
	{
	  if (num_msg > 1)
	    {
	      *name = strdup (resp[0].resp);
	      retval = pam_set_item (pamh, PAM_USER, resp[0].resp);
	      if (retval != PAM_SUCCESS)
		pam_syslog (pamh, LOG_ERR,
			    "pam_set_item (PAM_USER) failed with %d",
			    retval);
	    }
	  *password = strdup (resp[num_msg - 1].resp ?
			      resp[num_msg - 1].resp : "");
	}
      _pam_drop_reply (resp, num_msg);
    }
  else if (ask_user && !ask_password)
    {
      /* get the user name */
      retval = pam_get_user (pamh, name, NULL);
      if (retval != PAM_SUCCESS)
	{
	  pam_syslog (pamh, LOG_ERR, "pam_get_user failed: return %d", retval);
	  return (retval == PAM_CONV_AGAIN ? PAM_INCOMPLETE:retval);
	}
    }
  else if (ask_password && !ask_user)
   {
     char *cresp = NULL;

     retval = pam_prompt (pamh, PAM_PROMPT_ECHO_OFF, &cresp, _("Password: "));

     if (retval != PAM_SUCCESS)
       {
	 _pam_drop (cresp);
	 if (retval == PAM_CONV_AGAIN)
	   retval = PAM_INCOMPLETE;
	 return retval;
       }
     *password = strdup (cresp ? cresp : "");
     _pam_drop (cresp);
   }

  if (*password)
    {
      pam_set_item (pamh, PAM_AUTHTOK, *password);
      return PAM_SUCCESS;
    }

  return PAM_CONV_ERR;
}

int
__call_other_module(pam_handle_t * pamh, int flags,
			const char *mod_name, const char *func_name,
			options_t *options)
{
  const char *argv[4];
  char dl_path[PATH_MAX];
  void *dl_handle;
  int retval = PAM_IGNORE;
  int argc = 0;

  /* Give through some of our arguments to the called function.  */
  if (options->use_first_pass)
    argv[argc++] = "use_first_pass";
  if (options->debug)
    argv[argc++] = "debug";

  argv[argc] = NULL;

  snprintf (dl_path, sizeof (dl_path), "%s/pam_%s.so", PAMDIR, mod_name);

  dl_handle = dlopen (dl_path, RTLD_NOW);
  if (dl_handle == NULL)
    {
      pam_syslog (pamh, LOG_ERR,
		  "dlopen(\"%s\") failed: %s", dl_path, dlerror ());
    }
  else
    {
      int (*func) (pam_handle_t *, int, int, const char **);
      char *error;

      func = dlsym (dl_handle, func_name);
      if ((error = dlerror ()) != NULL)
	pam_syslog (pamh, LOG_ERR, "dlsym failed: %s", error);
      else
	{
	  retval = (*func)(pamh, flags, argc, argv);
	  if (options->debug)
	    pam_syslog (pamh, LOG_DEBUG, "pam_%s/%s() returned %d",
			mod_name, func_name, retval);
	}
#if 0
      dlclose (dl_handle);
#endif
    }

  return retval;
}

#if !defined(HAVE_PAM_SYSLOG)
/* syslogging function for errors and other information */
void
pam_syslog (pam_handle_t *pamh __attribute__ ((unused)), int err,
	    const char *format,...)
{
  va_list args;
  char *str;

  va_start (args, format);
  if (vasprintf (&str, format, args) < 0)
    return;
  syslog (err, "pam_unix2: %s", str);
  free (str);
  va_end (args);
}
#endif

/* static module data */
#ifdef PAM_STATIC
struct pam_module _pam_unix2_modstruct =
{
  "pam_unix2",
  pam_sm_authenticate,
  pam_sm_setcred,
  pam_sm_acct_mgmt,
  pam_sm_open_session,
  pam_sm_close_session,
  pam_sm_chauthtok
};
#endif
