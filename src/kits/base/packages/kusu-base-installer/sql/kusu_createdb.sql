# $Id$
#
#  Copyright (C) 2007 Platform Computing
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#


CREATE TABLE appglobals (
  agid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  kname VARCHAR(20) NULL,
  kvalue VARCHAR(255) NULL,
  ngid INTEGER UNSIGNED NULL DEFAULT NULL,
  PRIMARY KEY(agid)
);

CREATE TABLE components (
  cid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  kid INTEGER UNSIGNED NOT NULL,
  cname VARCHAR(255) NULL,
  cdesc VARCHAR(255) NULL,
  os VARCHAR(20) NULL,
  PRIMARY KEY(cid),
  INDEX components_FKIndex1(kid)
);

CREATE TABLE kits (
  kid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  rname VARCHAR(45) NULL,
  rdesc VARCHAR(255) NULL,
  version VARCHAR(20) NULL,
  isOS BOOL NULL DEFAULT 0,
  removeable BOOL NULL DEFAULT 0,
  arch VARCHAR(20) NULL,
  PRIMARY KEY(kid)
);

CREATE TABLE modules (
  mid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  ngid INTEGER UNSIGNED NOT NULL,
  module VARCHAR(45) NULL,
  loadorder INTEGER NULL DEFAULT 0,
  PRIMARY KEY(mid, ngid),
  INDEX modules_FKIndex1(ngid)
);

CREATE TABLE networks (
  netid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  network VARCHAR(45) NULL,
  subnet VARCHAR(45) NULL,
  device VARCHAR(20) NULL,
  suffix VARCHAR(20) NULL,
  gateway VARCHAR(45) NULL DEFAULT NULL,
  options VARCHAR(255) NULL,
  netname VARCHAR(255) NULL,
  startip VARCHAR(45) NULL,
  type VARCHAR(20) NOT NULL,
  inc INTEGER NULL DEFAULT 1,
  usingdhcp BOOL NULL DEFAULT 0,
  PRIMARY KEY(netid)
);

CREATE TABLE ng_has_comp (
  ngid INTEGER UNSIGNED NOT NULL,
  cid INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY(ngid, cid),
  INDEX ng_has_comp_FKIndex1(cid),
  INDEX ng_has_comp_FKIndex2(ngid)
);

CREATE TABLE ng_has_net (
  ngid INTEGER UNSIGNED NOT NULL,
  netid INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY(ngid, netid),
  INDEX net2ng_FKIndex1(netid),
  INDEX net2ng_FKIndex2(ngid)
);

CREATE TABLE nics (
  nicsid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  nid INTEGER UNSIGNED NOT NULL,
  netid INTEGER UNSIGNED NOT NULL,
  mac VARCHAR(45) NULL,
  ip VARCHAR(20) NULL,
  boot BOOL NULL DEFAULT 0,
  PRIMARY KEY(nicsid),
  INDEX nics_FKIndex1(nid),
  INDEX nics_FKIndex2(netid)
);

CREATE TABLE nodegroups (
  ngid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  repoid INTEGER UNSIGNED NOT NULL,
  ngname VARCHAR(45) NULL,
  installtype VARCHAR(20) NULL,
  ngdesc VARCHAR(255) NULL,
  nameformat VARCHAR(45) NULL,
  kernel VARCHAR(255) NULL,
  initrd VARCHAR(255) NULL,
  kparams VARCHAR(255) NULL,
  type VARCHAR(20) NOT NULL,
  PRIMARY KEY(ngid),
  INDEX nodegroups_FKIndex1(repoid)
);

CREATE TABLE nodes (
  nid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  ngid INTEGER UNSIGNED NOT NULL,
  name VARCHAR(45) NULL,
  kernel VARCHAR(255) NULL,
  initrd VARCHAR(255) NULL,
  kparams VARCHAR(255) NULL,
  state VARCHAR(20) NULL,
  bootfrom BOOL NULL,
  lastupdate VARCHAR(20) NULL,
  rack INTEGER UNSIGNED NULL DEFAULT 0,
  rank INTEGER UNSIGNED NULL DEFAULT 0,
  PRIMARY KEY(nid),
  INDEX nodes_FKIndex1(ngid)
);

CREATE TABLE packages (
  idpackages INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  ngid INTEGER UNSIGNED NOT NULL,
  packagename VARCHAR(255) NULL,
  PRIMARY KEY(idpackages, ngid),
  INDEX packages_FKIndex1(ngid)
);

CREATE TABLE partitions (
  idpartitions INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  ngid INTEGER UNSIGNED NOT NULL,
  device VARCHAR(255) NULL,
  partition VARCHAR(255) NULL,
  mntpnt VARCHAR(255) NULL,
  fstype VARCHAR(20) NULL,
  size VARCHAR(45) NULL,
  options VARCHAR(255) NULL,
  preserve VARCHAR(1) NULL,
  PRIMARY KEY(idpartitions, ngid),
  INDEX partitions_FKIndex1(ngid)
);

CREATE TABLE repos (
  repoid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  reponame VARCHAR(45) NULL,
  repository VARCHAR(255) NULL,
  installers VARCHAR(255) NULL,
  ostype VARCHAR(20) NULL,
  PRIMARY KEY(repoid)
);

CREATE TABLE repos_have_kits (
  repoid INTEGER UNSIGNED NOT NULL,
  kid INTEGER UNSIGNED NOT NULL,
  PRIMARY KEY(repoid, kid),
  INDEX repos_have_kits_FKIndex1(repoid),
  INDEX repos_have_kits_FKIndex2(kid)
);

CREATE TABLE scripts (
  idscripts INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  ngid INTEGER UNSIGNED NOT NULL,
  script VARCHAR(255) NOT NULL,
  PRIMARY KEY(idscripts, ngid),
  INDEX scripts_FKIndex1(ngid)
);

CREATE TABLE driverpacks (
  dpid INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
  cid  INTEGER UNSIGNED NOT NULL,
  dpname VARCHAR(255) NOT NULL,
  dpdesc VARCHAR(255) NULL,
  PRIMARY KEY(dpid),
  INDEX driverpacks_FKIndex1(cid)
);
