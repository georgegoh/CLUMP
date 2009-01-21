/*
 * Copyright (c) 2000, 2007 SuSE GmbH Nuernberg, Germany.
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

#define _GNU_SOURCE

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "passwd_nss.h"

#define PATH_NSWCONF "/etc/nsswitch.conf"

static FILE *nssfile = NULL;

static int
setnswent (void)
{
  if (nssfile)
    fclose (nssfile);

  nssfile = fopen (PATH_NSWCONF, "r");

  return (nssfile == NULL ? -1 : 0);
}

static void
endnswent (void)
{
  if (nssfile)
    {
      fclose (nssfile);
      nssfile = NULL;
    }
}

static struct nsw *
getnswent (void)
{
  struct nsw *nswb;
  char buf[1024];
  char *cp, *tmp;
  int count;

  if (!nssfile)
    setnswent ();


  if (nssfile == NULL)
    return NULL;

  nswb = calloc (1, sizeof (struct nsw));

  do {
    cp = fgets (buf, sizeof (buf), nssfile);
    if (cp == NULL)
      return NULL;

    tmp = strchr (cp, '#');
    if (tmp)
      *tmp = '\0';

    while (isspace (*cp))
      cp++;
  }
  while (*cp == '\0');

  tmp = cp;

  cp = strchr (cp, ':');
  if (!cp)
    return NULL;

  *cp++ = '\0';
  nswb->name = strdup (tmp);

  while (isspace (*cp))
    cp++;

  count = 3;
  nswb->orders = malloc ((count + 1) * sizeof (char *));
  for (nswb->orderc = 0; *cp; nswb->orderc++)
    {
      tmp = cp;

      while (!isspace (*cp) && *cp != '\0')
	++cp;

      if (*cp)
        *cp++ = '\0';

      if (nswb->orderc >= count)
        {
          count += 3;
          nswb->orders = realloc (nswb->orders, (count + 1) * sizeof (char *));
        }

      nswb->orders[nswb->orderc] = strdup (tmp);

      while (isspace (*cp))
        cp++;
    }

  nswb->orders[nswb->orderc] = NULL;

  return nswb;
}

void
nsw_free (struct nsw *ptr)
{
  int i;

  free (ptr->name);
  for (i = 0; i < ptr->orderc; ++i)
    free (ptr->orders[i]);

  free (ptr);

  return;
}

struct nsw *
_getnswbyname (const char *name)
{
  struct nsw *result;

  if (setnswent () != 0)
    {
      /* No nsswitch.conf, return "files".  */
      result = calloc (1, sizeof (struct nsw));
      if (result == NULL)
	return NULL;

      result->name = strdup (name);
      result->orderc = 1;
      result->orders = malloc (2 * sizeof (char *));
      result->orders[0] = strdup ("files");
      result->orders[1] = NULL;

      return result;
    }

  while ((result = getnswent ()) != NULL)
    {
      if (strcmp (name, result->name) == 0)
	{
	  endnswent ();
	  return result;
	}
      else
	nsw_free (result);
    }

  endnswent ();

  return NULL;
}
