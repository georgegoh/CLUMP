/*
 * Copyright (c) 2006, 2008 SUSE Linux Products GmbH, Nuernberg, Germany.
 * Copyright (c) 2002, 2003, 2004 SuSE GmbH Nuernberg, Germany.
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

#include <ctype.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <syslog.h>
#include <security/pam_modules.h>
#if defined (HAVE_SECURITY_PAM_EXT_H)
#include <security/pam_ext.h>
#endif

#include "public.h"
#include "logindefs.h"
#include "read-files.h"

const char *files_etc_dir = "/etc";

static void add_other_module(options_t *options, const char *name);

static void
parse_option (pam_handle_t *pamh, const char *argv,
	      const char *type, options_t *options)
{
  if (argv == NULL || argv[0] == '\0')
    return;

  if (strcasecmp (argv, "nullok") == 0)
    options->nullok = 1;
  else if (strcasecmp (argv, "use_first_pass") == 0)
    options->use_first_pass = 1;
  else if (strcasecmp (argv, "use_authtok") == 0)
    options->use_authtok = 1;
  else if (strncasecmp (argv, "nisdir=", 7) == 0)
    options->nisdir = strdup (&argv[7]);
  else if (strcasecmp (argv, "debug") == 0)
    {
      if (strcasecmp (type, "session") == 0)
	options->log_level = LOG_DEBUG;
      else
	options->debug = 1;
    }
  else if (strcasecmp (argv, "trace") == 0 &&
	   strcasecmp (type, "session") == 0)
    options->log_level = LOG_NOTICE;
  else if (strcasecmp (argv, "none") == 0 &&
	   strcasecmp (type, "session") == 0)
    options->log_level = -1;
  else if (strcasecmp (argv, "use_ldap") == 0)
    {
      add_other_module(options, "ldap");
    }
  else if (strcasecmp (argv, "use_krb5") == 0)
    {
      add_other_module(options, "krb5");
    }
  else if (strncasecmp (argv, "call_modules=", 13) == 0)
    {
      char *copy = strdup (&argv[13]), *arg;

      arg = copy;
      do
	{
	  char *cp = strchr (arg, ',');
	  if (cp)
	    *cp++ = '\0';

	  add_other_module (options, arg);
	  arg = cp;
	}
      while (arg);
      free (copy);
    }
  else
    pam_syslog (pamh, LOG_ERR, "Unknown option: `%s'", argv);
}

static void
add_other_module(options_t *options, const char *name)
{
  unsigned int i = 0;

  if (options->use_other_modules)
    {
      while (options->use_other_modules[i])
        i++;
    }

  options->use_other_modules = realloc(options->use_other_modules,
  				(i + 2) * sizeof(char *));
  options->use_other_modules[i++] = strdup(name);
  options->use_other_modules[i] = NULL;
}

int
get_options (pam_handle_t *pamh, options_t *options, const char *type,
	     int argc, const char **argv)
{
  /* Set some default values, which could be overwritten later.  */
  options->use_crypt = NONE;

  /* Parse parameters for module */
  for ( ; argc-- > 0; argv++)
    parse_option (pamh, *argv, type, options);

  return 0;
}
