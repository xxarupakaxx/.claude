document.querySelectorAll('[data-quiz]').forEach((quiz) => {
  const button = quiz.querySelector('button');
  const result = quiz.querySelector('.quiz-result');
  button?.addEventListener('click', () => {
    const expected = quiz.dataset.answer;
    const selected = quiz.querySelector('input:checked')?.value;
    const passed = selected === expected;
    result.textContent = passed
      ? '正解です。次に確認すべき証拠まで特定できています。'
      : 'もう一度確認してください。完了判定には成果物の存在だけでなく、acceptanceとevidenceの接続が必要です。';
    result.className = `quiz-result ${passed ? 'pass' : 'retry'}`;
    result.focus();
  });
});
