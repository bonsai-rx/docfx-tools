// This module contains common functions utilised by the Docfx Template System for Bonsai API pages.

exports.defineOperatorType = function defineOperatorType(model){
  // Define Bonsai operator types in documentation by checking for an explicit Category tag. If the class does not provide one,
  // check the inheritance tree of the class. 

  const checkForCategory = (category) => model.syntax?.content[0].value.includes(`[WorkflowElementCategory(ElementCategory.${category})]`);
  const checkInheritance = (inheritance) => model.inheritance?.some(inherited => inherited.uid.includes(inheritance));

  source = checkForCategory('Source') || checkInheritance('Bonsai.Source');
  sink = checkForCategory('Sink') || checkInheritance('Bonsai.Sink') || checkInheritance('Bonsai.IO.StreamSink') || checkInheritance('Bonsai.IO.FileSink');
  combinator = checkForCategory('Combinator') || checkInheritance('Bonsai.Combinator') || checkInheritance('Bonsai.WindowCombinator');
  transform = checkForCategory('Transform') || checkInheritance('Bonsai.Transform') || checkInheritance('Bonsai.Transform');

  let operatorType = {}
  operatorType.type = sink ? 'sink' : source ? 'source' : transform ? 'transform' : combinator ? 'combinator' :  false ; 
  operatorType.showWorkflow = !!operatorType.type

  return operatorType;
}