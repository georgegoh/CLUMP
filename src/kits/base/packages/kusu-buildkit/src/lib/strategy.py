from kusu.buildkit.strategies.tool01 import BuildKit as BuildKit01
from kusu.buildkit.strategies.tool02 import BuildKit as BuildKit02
from kusu.buildkit.strategies.tool03 import BuildKit as BuildKit03
from kusu.buildkit.strategies.tool04 import BuildKit as BuildKit04
from kusu.buildkit.strategies.kitsource01 import KusuComponent as KusuComponent01
from kusu.buildkit.strategies.kitsource01 import KusuKit as KusuKit01
from kusu.buildkit.strategies.kitsource01 import KitSrcFactory as KitSrcFactory01
from kusu.buildkit.strategies.kitsource02 import KusuComponent as KusuComponent02
from kusu.buildkit.strategies.kitsource02 import KusuKit as KusuKit02
from kusu.buildkit.strategies.kitsource02 import KitSrcFactory as KitSrcFactory02
from kusu.buildkit.strategies.kitsource03 import KusuComponent as KusuComponent03
from kusu.buildkit.strategies.kitsource03 import KusuKit as KusuKit03
from kusu.buildkit.strategies.kitsource03 import KitSrcFactory as KitSrcFactory03
from kusu.buildkit.strategies.kitsource04 import KusuComponent as KusuComponent04
from kusu.buildkit.strategies.kitsource04 import KusuKit as KusuKit04
from kusu.buildkit.strategies.kitsource04 import KitSrcFactory as KitSrcFactory04

KusuKitFactory = { '0.1': KusuKit01, '0.2': KusuKit02, '0.3': KusuKit03, '0.4': KusuKit04 }
KusuComponentFactory = { '0.1': KusuComponent01, '0.2': KusuComponent02, '0.3': KusuComponent03, '0.4': KusuComponent04 }
KitSrcAbstractFactory = { '0.1': KitSrcFactory01, '0.2': KitSrcFactory02, '0.3': KitSrcFactory03, '0.4': KitSrcFactory04 }

# Map of the strategies for creating a new kit template.
# The default strategy chosen is the latest version.
BuildKitNewStrategy = {'0.1': BuildKit01,
        '0.2': BuildKit02,
        '0.3': BuildKit03,
        '0.4': BuildKit04,
        'default': BuildKit04}

# Map of the strategies for making a kit. buildkit uses the
# build.kit file('api' field) to derive the make strategy.
# However, since the 'api' field was only introduced in version
# 0.2 and above, we set the default to the oldest strategy to
# cater for older build.kit files.
BuildKitMakeStrategy = {'0.1': BuildKit01,
        '0.2': BuildKit02,
        '0.3': BuildKit03,
        '0.4': BuildKit04,
        'default': BuildKit01}
