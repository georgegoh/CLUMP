#ifndef KUSU_ICE
#define KUSU_ICE

module kusu {
    module remote {
        struct ExceptionInfo {
            string title;
            string msg;
        };

        sequence<ExceptionInfo> ExceptionInfoSeq;

        exception InstallException {
            ExceptionInfoSeq messages;
        };

        interface ISetup {
            string install(string config) throws InstallException;
        };
    };
};

module kusu2 {
	sequence<string> StringArray;	
		
	module config {
			
		module net {
			
			struct DnsConfig {
				StringArray nameservers;
				string search;
				string domain;
			
			};
			
			exception NetworkException { };
			
			struct NetworkConfig{
				string ip;
				string name;
				string network;
				string netmask;
				string gateway;
				bool dhcp;
				bool enabledOnBoot;
			};
			
			interface INetwork {
			
				StringArray getInterfaces()
							 	throws NetworkException;
				
				NetworkConfig getInterfaceConfig(string interfaceName)
								throws NetworkException;
				
				void updateInterfaceConfig(NetworkConfig config)
								throws NetworkException;
							
                void createNameserverSettings()
	                            throws NetworkException;

			
			};
		};

        module sysinfo {
            struct OSInfo {
                string osName;
                string osVersion;
                string osArch;
            };

            exception SysInfoException{ };

            interface ISysInfo {
                OSInfo getOSInfo() throws SysInfoException;

                StringArray getSupportedOSs() throws SysInfoException;

            };

        };
		
	};
	 
};
#endif
