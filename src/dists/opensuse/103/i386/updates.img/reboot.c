#include <sys/reboot.h>
int main(int argc, char **argv) {
	reboot(RB_AUTOBOOT);
}
