import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const skill=process.env.BONGHWA_PRESENTATION_SKILL;
const runtime=process.env.BONGHWA_RUNTIME_ROOT;
process.env.RUNTIME_NODE_MODULES??=path.join(runtime,'node/node_modules');
const workspace=path.resolve(process.argv[2]);
const finalPath=path.resolve(process.argv[3]);
await fs.mkdir(path.dirname(finalPath),{recursive:true});
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
await finalizePresentation({
 workspaceDir:workspace,candidatePath:path.join(workspace,'candidate.pptx'),finalPath,
 explicitTotalSlideCount:11,requiredNativeTableOwnerSlides:[10],requiredNativeChartOwnerSlides:[],
 pythonExecutable:path.join(runtime,'python/bin/python3'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','10'],
 fontPolicy:{basis:'design',families:['Apple SD Gothic Neo','Courier New']},
 verifyArtifactToolImport:true,receiptPath:path.join(workspace,`${path.basename(finalPath)}.validation.json`),
});
console.log(finalPath);
