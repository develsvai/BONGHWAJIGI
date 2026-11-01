import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const skill=process.env.BONGHWA_PRESENTATION_SKILL;
const runtime=process.env.BONGHWA_RUNTIME_ROOT;
const workspace=path.resolve(process.argv[2]);
const finalPath=path.join(workspace,'output','bonghwajigi-architecture.pptx');
await fs.mkdir(path.dirname(finalPath),{recursive:true});
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const result=await finalizePresentation({
 workspaceDir:workspace,candidatePath:path.join(workspace,'candidate.pptx'),finalPath,
 explicitTotalSlideCount:3,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 pythonExecutable:path.join(runtime,'python/bin/python3'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-bullet-geometry','--validate-heading-fit'],
 fontPolicy:{basis:'design',families:['Apple SD Gothic Neo']},
 verifyArtifactToolImport:true,receiptPath:path.join(workspace,'validation.json'),
});
console.log(JSON.stringify({finalPath,ok:!!result}));
