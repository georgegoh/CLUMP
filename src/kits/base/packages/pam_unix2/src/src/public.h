/*
 * Copyright (c) 2006 SUSE Linux Products GmbH Nuernberg, Germany.
 * Copyright (c) 2003, 2004 SuSE Linux AG Nuernberg, Germany.
 * Copyright (c) 1999, 2000, 2002 SuSE GmbH Nuernberg, Germany.
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

#ifndef __PUBLIC_H__
#define __PUBLIC_H__

#include <pwd.h>
#include <grp.h>
#include <shadow.h>
#include <rpc/types.h>
#include <security/pam_modules.h>

#ifdef WITH_SELINUX
#include <selinux/selinux.h>
#endif

#ifdef ENABLE_NLS
#include <libintl.h>
#define _(String) dgettext("pam_unix2", String)
#else
#define _(String) (String)
#endif

#include "getuser.h"

enum crypt_t {NONE, DES, MD5, BIGCRYPT, BLOWFISH};
typedef enum crypt_t crypt_t;

struct options_t {
  int crypt_rounds;
  int debug;
  int log_level;
  int nullok;
  int use_authtok;
  int use_first_pass;
  char **use_other_modules;
  char *nisdir;
  crypt_t use_crypt;
};
typedef struct options_t options_t;

extern int c2n (char c);
extern long str2week (char *date);

extern int __get_tokens (pam_handle_t *pamh, int ask_user, int ask_password,
			 const char **name,
			 const char **password);
extern int __write_message (pam_handle_t *pamh, int flags, int msg_style,
			    const char *fmt, ...);
extern int __call_other_module(pam_handle_t * pamh, int flags,
			const char *mod_name, const char *func_name,
			options_t *options);

extern int get_options (pam_handle_t *pamh, options_t *options,
			const char *type, int argc, const char **argv);

/* Restore all attributes */
extern int copy_xattr (pam_handle_t *pamh, const char *from, const char *to);

#if !defined (HAVE_PAM_SYSLOG)
extern void pam_syslog (pam_handle_t *pamh, int err, const char *format,...);
#endif

#ifdef WITH_SELINUX
extern int selinux_check_access (const char *__chuser,
                                 unsigned int __access);
extern int set_default_context (pam_handle_t *pamh,
				const char *filename,
                                char **prev_context);
extern int restore_default_context (pam_handle_t *pamh, char *prev_context);
#endif

#ifndef PAM_AUTHTOK_RECOVERY_ERR
#define PAM_AUTHTOK_RECOVERY_ERR PAM_AUTHTOK_RECOVER_ERR
#endif

/* Good policy to strike out passwords with some characters not just
   free the memory */
#define _pam_overwrite(x)        \
do {                             \
     register char *__xx__;      \
     if ((__xx__=(x)))           \
          while (*__xx__)        \
               *__xx__++ = '\0'; \
} while (0)

/* Don't just free it, forget it too.  */
#define _pam_drop(X) \
do {                 \
    if (X) {         \
        free(X);     \
        X=NULL;      \
    }                \
} while (0)

#define _pam_drop_reply(/* struct pam_response * */ reply, /* int */ replies) \
do {                                              \
    int reply_i;                                  \
                                                  \
    for (reply_i=0; reply_i<replies; ++reply_i) { \
        if (reply[reply_i].resp) {                \
            _pam_overwrite(reply[reply_i].resp);  \
            free(reply[reply_i].resp);            \
        }                                         \
    }                                             \
    if (reply)                                    \
        free(reply);                              \
} while (0)

#endif /* __PUBLIC_H__ */
