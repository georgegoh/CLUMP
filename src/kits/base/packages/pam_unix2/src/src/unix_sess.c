/*
 * Copyright (c) 2006, 2008 SUSE Linux Products GmbH Nuernberg,Germany.
 * Copyright (c) 1999, 2000, 2002, 2003, 2004 SuSE GmbH Nuernberg, Germany.
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

#include <pwd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <syslog.h>
#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#include "public.h"

static int
pam_log_session (pam_handle_t *pamh, int flags, int argc,
		 const char **argv, const char *kind)
{
  int retval;
  const char *name;
  char *service, *tty, *rhost;
  options_t options;
  char *logmsg = NULL;

  memset (&options, 0, sizeof (options));
  options.log_level = -1; /* Initialize to default "none".  */

  if (get_options (pamh, &options, "session", argc, argv) < 0)
    {
      pam_syslog (pamh, LOG_ERR, "cannot get options");
      return PAM_SYSTEM_ERR;
    }

  /* get the user name */
  if ((retval = pam_get_user (pamh, &name, NULL)) != PAM_SUCCESS)
    return retval;

  if (name == NULL || name[0] == '\0')
    return PAM_SESSION_ERR;

  /* Move this after getting the user name, else PAM test suite
     will not pass ... */
  if (options.log_level == -1)
    return PAM_SUCCESS;

  retval = pam_get_item (pamh, PAM_SERVICE, (void *) &service);
  if (retval != PAM_SUCCESS)
    return retval;
  if (service == NULL)
    return PAM_CONV_ERR;

  retval = pam_get_item(pamh, PAM_TTY, (void *) &tty);
  if (retval !=PAM_SUCCESS)
    return retval;

  retval = pam_get_item(pamh, PAM_RHOST, (void *) &rhost);
  if (retval !=PAM_SUCCESS)
    return retval;

  if (tty && !rhost)
    {
      if (asprintf (&logmsg, "session %s for user %s: service=%s, tty=%s",
		    kind, name, service, tty) == -1)
	return PAM_SESSION_ERR;
    }
  else if (!tty && rhost)
    {
      if (asprintf (&logmsg,
		    "session %s for user %s: service=%s, rhost=%s",
		    kind, name, service, rhost) == -1)
	return PAM_SESSION_ERR;
    }
  else if (tty && rhost)
    {
      if (asprintf (&logmsg,
		    "session %s for user %s: service=%s, tty=%s, rhost=%s",
		    kind, name, service, tty, rhost) == -1)
	return PAM_SESSION_ERR;
    }
  else
    {
      if (asprintf (&logmsg, "session %s for user %s: service=%s",
		    kind, name, service) == -1)
	return PAM_SESSION_ERR;
    }

  pam_syslog (pamh, options.log_level, logmsg);
  free (logmsg);

  return PAM_SUCCESS;
}

int
pam_sm_open_session (pam_handle_t *pamh, int flags, int argc,
		     const char **argv)
{
  return pam_log_session (pamh, flags, argc, argv, "started");
}

int
pam_sm_close_session (pam_handle_t * pamh, int flags,
		      int argc, const char **argv)
{
  return pam_log_session (pamh, flags, argc, argv, "finished");
}
