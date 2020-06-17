0. first create sepsis category and assign sepsis = 1 for any category description with the word "sepsis" (regex) - keep the originals as will be required for below mergings. First row of csv.
1. ensure the programme understands the "remains" keyword in the ICD code column.
2. Run the exceptions in the "ICD10 preprocessing exceptions" sheet;
   * in the "ICD10 Codes" Column, watch out for spaces after the name (i.e. use .strip() when matching)
   * may need to remove the fullstop and create a new name when "keep" action is exectuted to avoid pruning automatically later
3. mark all diagnostic code outputs as a boolean True for a column called "exceptions"
   * i.e. all resulting codes - whether they are new categories or keeps - will be then kept and pruned under the default prune step. 
4. then run the default parent/prune ONLY on categories that do have the boolean exception label False		




|      Action   Name     |                                                                      What it should do                                                                     |                                                                         Example                                                                        |
|:----------------------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------:|
| default   prune | By default all ICD10 codes are   pruned after the full stop, unless they are in the exceptions in this csv file  "ICD10 Preprocessing Exceptions".   <br>Pruning is a special case of parent: pruning is merging everything after the full stop, parent is more granular merging. |                                      A01.x --> all of these e.g.   A01.1 and A01.2 are merged onto the parent A01                                      |
|          keep          |                                                   keep the ICD 10 code as it is   (do not prune or merge)                                                  |                                       A05.0 keep --> this remains a   separate independent diagnostic category.                                        |
|         parent         |                                    a special case of merging where   the category is merged with its one-level-up parent                                   | A08.31 parent --> merge   A08.31 to A08.3      <br>if instead we state A08.3x parent --> merge all numbers after A08.3 e.g.   A08.31 and A08.32 etc to A08.3 |
|          merge         |   merge two or more categories   into one. i.e. a logical OR between categories, whereby the result is a   single category usually with a different name. Delete original categories.   |        merge A04.0, A04.1, A04.2, A04.5, A04.71   to A04-Ecoli --> one new category is created A04-Ecoli from the others,   the the others are removed. <br>(Note not all numbers after full stop are merged therefore not pruning and not all the codes are directly related to parent e.g. A04.71 therefore not all of these merges are parent)       |

