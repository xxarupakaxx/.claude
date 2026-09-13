export const meta = {
  name: 'roadmap-sync',
  description: 'model-controlled argsからのRoadmap証跡を拒否するfail-closed境界',
  whenToUse: 'trusted local executor channelがないworkflowからRoadmap同期を要求するとき',
  phases: [{ title: 'Block', detail: '通常argsのreceiptを承認証跡として扱わない' }],
}

phase('Block')
return {
  success: false,
  reason: 'ROADMAP_TRUSTED_EXECUTOR_REQUIRED',
  detail: 'sync-roadmap.py must run through a non-model-controlled local executor',
}
